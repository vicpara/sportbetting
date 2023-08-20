import time
import os
import json
import pandas as pd
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from datetime import date, timedelta, datetime
import argparse

# get today's date and tomorrow's date
today = date.today().strftime("%Y-%m-%d")
tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

# set up Chrome options to remove "controlled by automated test software" message
options = webdriver.ChromeOptions()
options.add_argument("--dns-prefetch-disable");
options.add_argument("--disable-gpu");
options.add_argument("--disable-blink-features=AutomationControlled")
options.page_load_strategy = 'eager'
# create a Chrome driver instance with the options
driver = webdriver.Chrome(options=options)

# set implicit wait to 3 seconds for all elements to load before interacting with them
driver.implicitly_wait(2)
driver.set_page_load_timeout(20)

columns = ['No', 'Id', 'League', 'Home', 'Away',
           'MeciuriCuMax2goluri', 'MatchTime', 'Link']

##########################
# 1. Setezi data in script.
# 2. rulezi python 3SoccerWay.py --meciuri
# 3. rulezi python 3SoccerWay.py --stats

# Numele fisierului unde sa scriem rezultatele. Fiecare zi va fi un nou sheet in Excel
OUTPUT_FILE = 'matches.xlsx'

# data pentru care sa extragem meciurile
DATA = '2023/08/20'


parser = argparse.ArgumentParser(description='Procesam meciurile si statisticile lor')

# Meciuri
parser.add_argument('--meciuri', action='store_true', help='Listeaza toate ')

# Statistici
parser.add_argument('--stats', action='store_true', help='Extrage statisticile meciurile extrase in pasul 1 `--meciuri` meciuri')
args = parser.parse_args()



# Load the existing XLSX file
open_mode = 'w'
sheet_exist_mode = None
if os.path.exists(OUTPUT_FILE):
    open_mode = 'a'
    sheet_exist_mode = 'replace'

with pd.ExcelWriter(path=OUTPUT_FILE, engine='openpyxl', mode=open_mode, if_sheet_exists=sheet_exist_mode) as writer:
    sheet_name = DATA.replace('/', '-')
    df_matches = pd.DataFrame(columns=columns)
    if open_mode == 'a':
        book = writer.book
        if sheet_name in book.sheetnames:
            df_matches = pd.read_excel(
                OUTPUT_FILE, sheet_name=sheet_name, engine='openpyxl')

    ########################################################
    # SCHIMBA AICI
    # URL_ul cu data care trebuie procesata
    url = 'https://int.soccerway.com/matches/' + DATA
    driver.get(url)
    print('Procesam URL: ', url)

    ########################################################
    # wait for the page to load completely (here, 5 seconds are waited)
    time.sleep(1)
    print('Acceptam cookiesurile')
    # Accept cookies
    driver.find_elements('css selector', 'button[mode="primary"]')[0].click()
    time.sleep(1)
    print('   Am acceptat')


    if args.meciuri:
        print('### EXTRAGEM TOATE MECIURILE pentru data de  ', DATA)
        # Run JAVASCRIPT to expand all groups
        print('Rulam javascript in browser pentru a expanda toate grupurile de meciuri. Apoi asteptam sa termine treaba.')
        js_script_expand_all_groups = '''
        let toatetarile = document.querySelectorAll('#livescores > div.livescores-comps > div.livescores-comp')

        const TIMPASTEPTARE_INTRE_GRUPURI= 50 //milisecunde
        Array.from(toatetarile).forEach((tara,i) => 
            setTimeout(() => {
            if(tara.getAttribute('data-expanded')=="1") return
            tara.querySelector('h2 button.expand-icon').click()
        }, i*TIMPASTEPTARE_INTRE_GRUPURI))
        '''
        driver.execute_script(js_script_expand_all_groups)
        time.sleep(60)
        print('\tAm rulat. Daca sunt multe meciuri e nevoie sa asatepta mai mult timp. Daca mai exista grupuri in pagina ne-expandate regleaza asteptarea de mai sus.')

        ####################################################
        # get date from page
        page_date = driver.find_element(
            By.CSS_SELECTOR, 'div#livescores').get_attribute('data-date')

        index = 0
        matches = []
        league_roots = driver.find_elements(By.CSS_SELECTOR, 'div.livescores-comp')
        print('Am gasit in pagina data de: ', page_date,
            ' urmatorul nr de campinate:', len(league_roots))
        for league in league_roots:
            league_name = league.find_element(By.CSS_SELECTOR, 'h2 > a').text
            # find all HTML elements that contain match information

            match_elements = league.find_elements("css selector", 'div.matchinfo')
            for el in match_elements:
                try:
                    match_time = el.find_element(
                        By.CSS_SELECTOR, "div.timebox > time").get_attribute("datetime")
                    home_team = el.find_element(
                        By.CSS_SELECTOR, "div.team_a").text.strip()
                    away_team = el.find_element(
                        By.CSS_SELECTOR, "div.team_b").text.strip()
                    link = el.find_element(
                        By.CSS_SELECTOR, "div.teams > a").get_attribute("href")
                    print(
                        f"{index:<3}  {league_name:<30}  {match_time} {home_team:<25} vs. {away_team:<25}")
                    id = home_team + '.' + away_team

                    if id not in df_matches['Id'].values:
                        matches.append({'Id': id, 'No': index, 'League': league_name, 'Home': home_team, 'Away': away_team,
                                        'MatchTime': match_time, 'MeciuriCuMax2goluri': -1, 'Link': link})
                        index += 1

                except Exception as e:
                    print('Eroare', e)
                    pass

        df_matches = df_matches.append(matches, ignore_index=True)
        df_matches.to_excel(writer, sheet_name=sheet_name, index=False)
        print('Saved to xlsx file:', OUTPUT_FILE)



    ####################################################
    # partea 2 - extragere golaveraj din fiecare pagina.
    if args.stats:
        print('### EXTRAGEM STATISTICILE pentru fiecare din MECIURILE gasite in pasul anterior, pentru data', DATA)
        now_ts = int(datetime.now().timestamp())
        print('#############\nTrecem la partea interesanta. Luam fiecare pagina la rand si extragem golaverajul.\n')
        print('Avem de procesat ', df_matches.shape[1], 'meciuri')
        for index, m in df_matches.iterrows():
            try:
                print('##', index, 'Procesam ', ':',  m['Home'], '-', m['Away'])
                if m['Link'].endswith('/head2head/'):
                    continue
                count = 0
                h2h_comparasion_link = m['Link'].rstrip('/') + '/head2head/'
                print('\t', h2h_comparasion_link)
                driver.get(h2h_comparasion_link)
                print('\t\t', 'ok')
                # Așteaptă ca pagina să se încarce complet (1 secunda)
                time.sleep(0.8)
                matches_table_row = driver.find_elements(
                    By.CSS_SELECTOR, 'div.block_h2hsection_head2head table.matches tbody tr')
                for row in matches_table_row:
                    try:
                        match_ts = row.get_attribute('data-timestamp')
                        if match_ts > str(now_ts) and match_ts < '1600000000':
                            continue
                        score_cell = row.find_element(By.CSS_SELECTOR, 'td.score')
                        score = score_cell.text.strip()
                        if score[0].isalpha() or score[-1].isalpha() :
                            continue
                        goals = sum(map(lambda e: int(e), map(
                            lambda e: e.strip(), score.split('-'))))
                        if goals > 2:
                            break
                        count += 1
                    except selenium.common.exceptions.NoSuchElementException:
                        continue

                print('\t Nr meciuri cu golaveraj sub 2:', count)
                m['MeciuriCuMax2goluri'] = count
                df_matches.at[index, 'MeciuriCuMax2goluri'] = count
                df_matches.at[index, 'Link'] = h2h_comparasion_link
            except Exception as ex:
                print('Error', ex)
                continue

            df_matches.to_excel(writer, sheet_name=sheet_name, index=False)

        df_matches.to_excel(writer, sheet_name=sheet_name, index=False)
        print('Saved to xlsx file:', OUTPUT_FILE)

exit(1)

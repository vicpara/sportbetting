import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from datetime import date, timedelta, datetime

# get today's date and tomorrow's date
today = date.today().strftime("%Y-%m-%d")
tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

# set up Chrome options to remove "controlled by automated test software" message
options = webdriver.ChromeOptions()

options.add_argument("--disable-blink-features=AutomationControlled")
# create a Chrome driver instance with the options
driver = webdriver.Chrome(options=options)

# set implicit wait to 10 seconds for all elements to load before interacting with them
driver.implicitly_wait(10)

########################################################
# SCHIMBA AICI
# URL_ul cu data care trebuie procesata
url = 'https://int.soccerway.com/matches/2023/08/19/'
driver.get(url)

########################################################
# wait for the page to load completely (here, 5 seconds are waited)
time.sleep(5)

print('Acceptam cookiesurile')
# Accept cookies
driver.find_elements('css selector', 'button[mode="primary"]')[0].click()
time.sleep(1)
print('   Am acceptat')


# Run JAVASCRIPT to expand all groups
print('Rulam javascript in browser pentru a expanda toate grupurile de meciuri. Apoi asteptam sa termine treaba.')
js_script_expand_all_groups = '''
let toatetarile = document.querySelectorAll('#livescores > div.livescores-comps > div.livescores-comp')

const TIMPASTEPTARE_INTRE_GRUPURI= 150 //milisecunde
Array.from(toatetarile).slice(0,20).forEach((tara,i) => 
  setTimeout(() => {
  tara.querySelector('h2h comparasion button').click()
}, i*TIMPASTEPTARE_INTRE_GRUPURI))
'''
driver.execute_script(js_script_expand_all_groups)
time.sleep(10)
print('     Am rulat. Daca sunt multe meciuri e nevoie sa asatepta mai mult timp. Daca mai exista grupuri in pagina ne-expandate regleaza asteptarea de mai sus.')

####################################################
# get date from page
page_date = driver.find_element(
    By.CSS_SELECTOR, 'div#livescores').get_attribute('data-date')
print('Am gasit in pagina data de: ', page_date)

# find all HTML elements that contain match information
match_elements = driver.find_elements("css selector", 'div.matchinfo')
# create an empty list to add matches that are today or tomorrow
matches = []
url_str = '-'.join(url.split('soccerway.com')[1].split('/'))
out_text = f'meciuri-{url_str}.txt'
with open(out_text, 'w', encoding='utf-8') as f:
    f.write(f"Data paginii: {page_date}\n")
    f.write(f"{'Acasa':<25} {'Deplasare':<25} {'Data':<25} Link\n")
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
            print(f"{match_time} {home_team:<25} vs. {away_team:<25}")
            f.write(f"{home_team:<25} {away_team:<25} {match_time:<25} {link}\n")
            matches.append({'home': home_team, 'away': away_team,
                           'datetime': match_time, 'link': link})

        except Exception as e:
            # do something in case the date or time element is not found
            print('Eroare', e)
            pass
print('OK. Am scris rezultate TEXT la ', out_text)

out_json = f'meciuri-{page_date}.json'
with open(out_json, 'w') as fp:
    json.dump(matches, fp)
print('OK. Am scris rezultate in JSON la ', out_json)

####################################################
# partea 2 - extragere golaveraj din fiecare pagina.
# din pacate nu merge inca..mai lucrez.
print('Trecem la partea interesanta. Luam fiecare pagina la rand si extragem golaverajul.')

matches_with_stats = []
for m in matches:
    print('\nProcesam ', m['home'], ' vs. ', m['away'], m)
    count = 0
    h2h_comparasion_link = m['link'].rstrip('/') + '/head2head/'
    driver.get(h2h_comparasion_link)
    # Așteaptă ca pagina să se încarce complet
    # # wait for the page to load completely (here, 5 seconds are waited)
    time.sleep(5)

    now_ts = int(datetime.now().utcnow())
    matches_table_row = driver.find_elements(
        By.CSS_SELECTOR, 'div.block_h2h_matches table.matches tbody tr')
    for row in matches_table_row:
        print('ROW', row)
        match_ts = int(row.get_attribute('data-timestamp'))
        if match_ts > now_ts:
            continue
        score_cell = row.find_element(By.CSS_SELECTOR, 'td.score')
        score = score_cell.text.strip().split
        goals = sum(map(lambda e: int(e), map(lambda e: e.strip(), score.split('-'))))
        if goals > 2:
            break
        count+=1
        
    if ()

        # Așteaptă ca pagina să se încarce complet
        # wait for the page to load completely (here, 5 seconds are waited)
    time.sleep(5)

    # Extrage informațiile despre golaveraj din subpagina "head2head"
    goals_table = driver.find_elements(By.CSS_SELECTOR, 'table.matches')[0]
    rows = goals_table.find_elements(By.CSS_SELECTOR, 'tbody > tr')

    home_goals = []
    away_goals = []

    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        home_goals.append(int(cells[1].text.strip()))
        away_goals.append(int(cells[2].text.strip()))

        # Verifică dacă meciurile îndeplinesc condiția de a marca sub 2 goluri în ultimele 4 meciuri
    if len(home_goals) >= 3 and sum(home_goals[-3:]) < 6 and len(away_goals) >= 3 and sum(away_goals[-3:]) < 6:
        matches_with_stats.append(m)

    history = {}
    home = []
    away = []
    for pm in past_matches:
        try:
            home_team = pm.find_element(
                By.CSS_SELECTOR, 'td.team-a ').text.strip()
            away_team = pm.find_element(
                By.CSS_SELECTOR, 'td.team-b > a').text.strip()
            score = pm.find_elements(By.CSS_SELECTOR, 'td.score')
            if len(score) > 0:
                score = score[0].text.strip()
            else:
                continue
            home_score = int(score.split(' - ')[0].strip())
            away_score = int(score.split(' - ')[1].strip())

            for_team = {m['home'], m['away']}.intersection(
                {home_team, away_team})
            line = {home_team: home_score,
                    away_team: away_score, 'for': for_team}

            if for_team == m['home']:
                home.append(line)
            else:
                away.append(line)

            print(line)
            matches_with_stats.append(
                {'home': m['home'], 'away': m['away'], 'home_score': home_score, 'away_score': away_score})
        except Exception as e:
            print('Eroare', e)
            pass
    history['home'] = home
    history['away'] = away
    m['history'] = history
    matches_with_stats.append(m)


out_json = f'meciuri-cu-stats-{page_date}.json'
with open(out_json, 'w') as fp:
    json.dump(matches_with_stats, fp)
print('OK. Am scris rezultate in JSON la ', out_json)


exit(1)

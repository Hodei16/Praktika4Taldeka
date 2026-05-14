# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper


class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def check_credentials(self, username, password, event=None):
        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        erabiltzailea = username.get() if hasattr(username, 'get') else username
        pasahitza = password.get() if hasattr(password, 'get') else password

        saioa = requests.Session()
        sarrera_uri = "https://egela.ehu.eus/login/index.php"
        hasierako_erantzuna = saioa.get(sarrera_uri)
        sare_azterketa = BeautifulSoup(hasierako_erantzuna.text, 'html.parser')
        login_tokena = sare_azterketa.find('input', {'name': 'logintoken'})['value']

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        datuak = {'username': erabiltzailea, 'password': pasahitza, 'logintoken': login_tokena}
        post_erantzuna = saioa.post(sarrera_uri, data=datuak, allow_redirects=False)

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        if 'Location' in post_erantzuna.headers:
            birbideratze_erantzuna = saioa.get(post_erantzuna.headers['Location'], allow_redirects=False)
        else:
            birbideratze_erantzuna = post_erantzuna

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        if 'Location' in birbideratze_erantzuna.headers:
            azken_erantzuna = saioa.get(birbideratze_erantzuna.headers['Location'])
        else:
            azken_erantzuna = birbideratze_erantzuna

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if "Log out" in azken_erantzuna.text or "Irten" in azken_erantzuna.text:
            self._login = 1
            self._cookie = saioa.cookies
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        nire_orria = requests.get("https://egela.ehu.eus/", cookies=self._cookie)
        nire_azterketa = BeautifulSoup(nire_orria.content, "html.parser")

        for esteka in nire_azterketa.find_all('a', href=True):
            testua = esteka.get_text().lower()
            if "web sistemak" in testua or "sistemas web" in testua:
                self._curso = esteka['href']
                break

        ikastaro_orria = requests.get(self._curso, cookies=self._cookie)
        ikastaro_azterketa = BeautifulSoup(ikastaro_orria.content, "html.parser")
        baliabideak = ikastaro_azterketa.find_all('a', href=lambda h: h and "resource/view.php" in h)

        if len(baliabideak) > 0:
            urratsa = float(100.0 / len(baliabideak))
        else:
            urratsa = 100

        for baliabidea in baliabideak:
            izena_etiketa = baliabidea.find('span', class_='instancename')
            if izena_etiketa:
                izena_garbia = izena_etiketa.get_text(strip=True).replace(' Archivo', '').replace(' Fitxategia', '')
                self._refs.append({'pdf_name': izena_garbia + '.pdf', 'pdf_link': baliabidea['href']})

            progress += urratsa
            progress_var.set(progress)
            progress_bar.update()
            time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):
        pdf_esteka = self._refs[selection]['pdf_link']
        pdf_izena = self._refs[selection]['pdf_name']

        baliabide_orria = requests.get(pdf_esteka, cookies=self._cookie)

        if 'application/pdf' in baliabide_orria.headers.get('Content-Type', ''):
            pdf_edukia = baliabide_orria.content
        else:
            baliabide_azterketa = BeautifulSoup(baliabide_orria.content, "html.parser")
            objektua = baliabide_azterketa.find('object', {'id': 'resourceobject'})

            if objektua and 'data' in objektua.attrs:
                fitxategi_esteka = objektua['data']
            else:
                ordezko_esteka = baliabide_azterketa.find('a', href=lambda h: h and 'pluginfile.php' in h)
                fitxategi_esteka = ordezko_esteka['href'] if ordezko_esteka else pdf_esteka

            pdf_edukia = requests.get(fitxategi_esteka, cookies=self._cookie).content

        return pdf_izena, pdf_edukia
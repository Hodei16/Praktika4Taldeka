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

        saioa = requests.Session()
        sarrera_uri = "https://egela.ehu.eus/login/index.php"
        hasierako_erantzuna = saioa.get(sarrera_uri)
        sare_azterketa = BeautifulSoup(hasierako_erantzuna.text, 'html.parser')
        login_tokena = sare_azterketa.find('input', {'name': 'logintoken'})['value']

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        datuak = {'username': username, 'password': password, 'logintoken': login_tokena}
        post_erantzuna = saioa.post(sarrera_uri, data=datuak, allow_redirects=False)

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        birbideratze_erantzuna = saioa.get(post_erantzuna.headers['Location'], allow_redirects=False)

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        azken_erantzuna = saioa.get(birbideratze_erantzuna.headers['Location'])

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

        nire_orria = requests.get("https://egela.ehu.eus/my/", cookies=self._cookie)
        nire_azterketa = BeautifulSoup(nire_orria.content, "html.parser")

        for esteka in nire_azterketa.find_all('a'):
            if esteka.text and "Sistemas Web" in esteka.text:
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
                izena = izena_etiketa.text.split(' Archivo')[0]
                ikonoa = baliabidea.find('img')
                if ikonoa and "pdf" in ikonoa['src']:
                    self._refs.append({'pdf_name': izena + '.pdf', 'pdf_link': baliabidea['href']})

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
        baliabide_azterketa = BeautifulSoup(baliabide_orria.content, "html.parser")
        fitxategi_esteka = baliabide_azterketa.find('object', {'id': 'resourceobject'})['data']
        pdf_edukia = requests.get(fitxategi_esteka, cookies=self._cookie).content

        return pdf_izena, pdf_edukia
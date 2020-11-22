#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 08:42:51 2020

@author: ICARD
"""
#module systeme:
import re
import time
import os.path
import os
import urllib.parse
import mimetypes
#module interne :
import config_srv

def traite_client(sock_client,adr):
    '''
    Dans la fonction traite_client c'est ici que l'on s'occupe de faire appel à la quasi totalité des fonctions du module client_http.
    On inclu cette fonction dans un try qui permettrait de recupérer une erreur qui nous aurait échappé avant (On est jamais trop prudent)
    Ensuite on fait appel a la fonction lecture_requete pour recuperer la requete du client.
    la requete est renvoyer à la fonction verifie requete pour en extraire un code (200 si tout va bien, 400,404,500 etc... sinon)
    En fonction de ce code :
        Soit le code est 200 et alors on traite la requete en construisant le chemin,
        avec construit_chemin_fichier en lui indiquant le fichier demandé par le client.
        ensuite on recupére l'entete et les données renvoyer par la fonction lecture_donnees,
        on encode l'entete en binaire et on return le tout.
        
        Sinon c'est qu'il y'a une erreur, auquel cas on genere l'entete avec le code de l'erreur,
        On va recuperer les donnees lié à cette erreur avec la fonction genere_donnees_erreur,
        et on return le tout.
    '''
    
    try : 
        print("traitement du client")
        data=lecture_requete(sock_client)
        code=verifie_requete(data)
        if code == 200 : 
            ligne1=data.split('\r\n')
            ligne1=ligne1[0]
            chemin = construit_chemin_fichier(ligne1)
            entete,donnees = lecture_donnees(chemin)
            reponse = str.encode(entete) + donnees
        else :
            reponse = str.encode(genere_entete(code,None,'text/html; charset=utf-8')) + genere_donnees_erreur(code)
    except OSError : 
        print ('Problème client_http')
        
    
    try : 
        sock_client.sendall(reponse) #renvoie de la reponse au client
    except OSError :
        print("Erreur d'émission")
    

def lecture_requete(s):
    """
    La fonction lecture_requete recupère la requete envoyé par le client.
    La fonction reçois la requete par 1024 octets.
    Elle stock dans la variable 'data'.
    Ensuite elle s'assure d'avoir reçu toute la requete pour cela :
            elle verifie à chaque fois si les derniers caractère reçu correspondent à ceux de fin d'une requete ('\r\n\r\n').
            Si c'est le cas elle change la valeur de la variable play qui permet de sortir de la boucle while.
    Enfin elle change la variable data qui est une chaine binaire en chaine de caractère.
    Mais il est aussi possible que par malheur le client renvoie un chaine binaire vide:
        Si c'est le cas on incrémente un compte pour gerer l'erreur s'il y'en a une.
    parametre s : socket utilisé pour la communication par le serveur.
    return : data la variable contenant la requete
    """
    max_octets=1024
    play=False
    compteur = 0
    data=b'' #definition d'une chaine binaire vide
    while (play==False) :
        try:
            data+=s.recv(max_octets) #reception
        except OSError as e:
            print('Erreur de reception')
            
        if data==b'' :
            compteur += 1
        if compteur >=3 :
            return data
        
        if data[-4:]==b'\r\n\r\n': #verification d'une caractère de fin de requete
            play=True
    data=data.decode() #changement en chaine de caractère

    return data
    
def verifie_requete(req):
    """
    La fonction verifie_requete permet de s'assurer que la syntaxe de la requete est conforme est bonne.
    Pour cela : On verifie que la requete n'est une chaine binaire vide sinon cela veut dire que c'est une erreur.
                on decoupe la requete ligne par ligne dans une liste (req)
                on redecoupe la ligne n°1 mot par mot dans une liste (text1)
                on vérifie que la ligne n°1 comporte bien 3champs.
                on verifie que :
                                 le 1er mot de la ligne n°1 est bien 'GET'
                                 le dernier mot de la ligne n°1 est bien la déclaration d'HTTP
                Ensuite on verifie à l'aide de la methode re.fullmatch la syntaxe des lignes suivante
                verification : 1ere lettre -> Majuscule ou Minuscule
                               La suite sont des lettres minuscules, majuscules ou un tiret
                               Ensuite le caractère ':'
                               Enfin des carctères quelconques.
    Enfin à tout ces resultats on associe un code d'etat HTTP : 
                200 : Réponse positive
                400 : Requête mal formée
                405 : Méthode non prise en charge
                500 : Erreur interne du serveur
                
    parametre 'req': correspond à la requete recu par le serveur
        
    """
    if req == b'' : 
        return 500
    
    req=req.split('\r\n')
    text1=req[0].split()
    
    #verif ligne 1
    if len(text1)!=3:
        return 400
    if text1[0]!='GET':
        return 405
    if text1[2]!='HTTP/1.1' and text1[2]!='HTTP/1.0' :
        return 500
        
    #On commence à 1 car la premiere ligne a déja été traité et on va jusqu'a -2 car les 2derniers caracteres sont des chaines vides
    for i in range (1,len(req)-2):
        if re.fullmatch(r"^[A-Z a-z][a-z A-z -]*[:].*",req[i])==None: #verification de la syntaxe
            return 400
        
    return 200


def genere_entete(code_reponse, taille, type_mime):
    '''
        La fonction genere_entete permet de generer l'entete de la reponse que vas renvoyer notre serveur
        elle construira cette entete en chaine de caractere en plusieure étape : 
            1er étape : elle vérifie si le code réponse est un code réponse connu (réferencé dans le dictionnaire 
            CODE_ETAT dans le module config_srv) si ce n'est pas le cas elle met la valeur de ce code a 500.
            
            2ème étape : elle construit la premiere ligne en y mettant le champs 'HTTP/1.1'
            suivi du code de réponse et de son message associé.
            
            3ème étape : Elle construit le champs 'Date' en respectant la syntaxe de ce champs.
            
            4ème étape : elle construit le champs 'Server' en y indiquant le nom du serveur.
            
            5ème étape : Elle construit le champs 'Connexion' avec 'close' qui indiquera la fermeture 
            de la connexion apres l'échange.
            
            6ème étape : Elle construit le champs 'Content-Length' avec la taille du message qui va suivre 
            seulement si la taille a été donné à la fonction 
            
            7éme étape : Elle construit le champs 'Content-Type'
            
            8ème étape : Elle rajoute '\r\n\r\n' pour indiqué la fin de l'entete.
            
            Parametre : code_reponse correspond au code réponse renvoyé par la fonction verifie_requete
                        taille correspond à la taille du message à comuniquer
                        
            Return : Une chaine de caractère contenant l'entete de la reponse.
    '''
    
    if code_reponse not in config_srv.CODE_ETAT :
        code_reponse=500
    
    #ligne n°1 :
    code_reponse_str=str(code_reponse)
    reponse = 'HTTP/1.1'
    reponse += ' ' + code_reponse_str
    reponse += ' ' + config_srv.CODE_ETAT[code_reponse] + '\r\n'
    
    #date : 
    time1=time.localtime()
    reponse += 'Date: '
    reponse += time.strftime('%A',time1) + ',' + ' '
    reponse += time.strftime('%d',time1)  + ' '
    reponse += time.strftime('%b',time1)  + ' '
    reponse += str(time1[0])  + ' '
    reponse += str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\n'
    
    #Nom du serveur :  
    reponse += 'Server: '
    reponse += 'server_icard' + '\r\n'
    
    #Connection : 
    reponse += 'Connection: '
    reponse += 'close' + '\r\n'
    
    #Content-Length
    if taille != None : 
        reponse += 'Content-Length: '
        reponse += str(taille) + '\r\n'
    
    #Content-type :  
    reponse += 'Content-Type: '
    reponse += type_mime + '\r\n'
    
    #fin de l'entete : 
    reponse += '\r\n'
    
    return reponse


def genere_donnees_erreur(code):
    '''
    La fonction genere_donnees_erreur permet de generer les pages html associé au code d"erreur.
    Le code html ce trouve dans un dictionnaire dans le module config_srv.
    '''
    if code not in config_srv.PAGE_HTML_ERREUR :
        code=500
    return config_srv.PAGE_HTML_ERREUR[code]


def construit_chemin_fichier(ligne1_entete):
    '''
    La fonction construit_chemin_fichier permet d'indiquer ou le chemin à suivre,
    pour atteindre le fichier HTML demandé par le client.
    Fonctionnement : 
        1. On récupère le debut du chemin dans le quel tout les fichiers sont stockés
        2. On récupere le nom du fichier demandé par le client.
        3. On vérifie si le nom du fichier possède des '?' si c'est le cas on supprime tout ce qui suit.
        4. On nettoie la chaine au cas ou elle contiendrais des caractères spéciaux ('%' 'nn' etc...)
        5. On verifie si le nom du fichier demander ce termine par un '/' dans ce cas la le client,
           a indiqué un dossier et donc nous lui fournirons le fichier HTML 'index.HTML' du dossier demandé,
           puis on reconstruit le chemin entier.
        6.Si la condition precédente n'est pas vrai on reconstruit le chemin.
        
        Paramètre ligne1_entete : correspond à la 1ere ligne de la requete envoyer par le client.
        Return : on retourne le chemin final menant au fichier demandé par le client.
    '''
    
    #initialisation des variables
    repertoire = config_srv.get_config('rep_servi') 
    ligne1_entete = ligne1_entete.split()
    new_chemin=ligne1_entete[1]
    
    #vérification du caractère '?'
    for car in ligne1_entete[1] :
        if car == '?':
            new_chemin = ligne1_entete[1].split('?')
            new_chemin = new_chemin[0]
    
    #nettoyage de la chaine
    new_chemin = urllib.parse.unquote(new_chemin)
    
    #vérification du dernier caractère & reconstruction final de la chaine
    if new_chemin[-1] == '/':
        new_chemin = repertoire + os.path.join(new_chemin, 'index.html')
    
    #reconstruction final de la chaine
    else :
        new_chemin = repertoire + new_chemin
    
        
    return new_chemin


def lecture_donnees(nom_fichier):
    '''
    La fonction lecture_donnees permet de lire le contenue du fichier qui a été demander par le client.
    Pour cela 3 cas peuvent ce présenter : 
                                         - Cas n°1 : Le fichier existe (le meilleurs cas possible)
                                         - Cas n°2 : Le fichier n'existe pas
                                         - Cas n°3 : Le fichier n'est pas lisible
    On commence par un try qui vas permettre de verifier si une Exception est generé lors du programme : 
            Si c'est le cas, cela correspond au Cas n°3
            On renverra donc l'entete et les donnees correspondante à une erreur 500
    
    Ensuite on commence par verifier que le fichier existe, sinon on se trouve en presence du Cas n°2,
    pour cela on renverra donc l'entete et les donnees correspondante à une erreur 404.
    
    Si le fichier existe et qu'il est lisible alors aucun probleme, on lis le fichier 
    et on renvoie l'entete d'un code 200 accompagnée des donnees du fichier lue.
    
    Dans cette fonction on fait appel a la fonction genere_entete : 
        pour generer l'entete de la reponse avec 2 parametre : le code et la taille de la reponse.
        La taille de la reponse n'est donnée que dans le cas n°1 c'est pourquoi on utilise os.path.getsize.
    
    Paramètre nom_fichier : correspond au chemin du fichier demandé.
    Return entete_lecture : est un tuple comprenant l'entete et les données de la reponse.
    
    
    '''
    try : 
        if os.path.isfile(nom_fichier) == True:
    
            with open (nom_fichier, 'r+b') as f:
                donnees = f.read()
                length = os.path.getsize(nom_fichier)
            entete = genere_entete(200, length, type_contenu(nom_fichier))
            entete_lecture=(entete, donnees)
            
        else : 
            entete = genere_entete(404, None, 'text/html; charset=utf-8')
            donnees = config_srv.PAGE_HTML_ERREUR[404]
            entete_lecture=(entete, donnees)
    except OSError : 
         entete = genere_entete(500, None, 'text/html; charset=utf-8')
         donnees = config_srv.PAGE_HTML_ERREUR[500]
         entete_lecture=(entete, donnees)
        
    return entete_lecture
        

def type_contenu(chemin_fichier):
    '''
    La fonction type_contenu permet de verifier le type du fichier demandé par le client.
    Pour cela on se sert du module mimetypes qui renvoie un tuple contenant le type et l'encodage du fichier donné en argument.
    D'abord on s'assure que l'argument envoyé à la fonction est bien une chaine de caractère et que le fichier existe sinon,
    on return 'text/html; charset=utf-8' qui est la valeur de base du champ Content-type.
    Ensuite on appel la fonction guess_type du module mimetypes en lui donnant la variable chemin_fichier.
    qui nous retournera un tuple qu'on stockera séparement dans les variable type_fichier et encodage.
    Forcé de constater que encodage est tres souvent égal a None si c'est le cas on renvoie 'charset=None' sinon on renvoie le bon encodage
    Enfin on return la variable retour qui stock le bon type/soustype et charset à placer dans le champ content-type.
    '''
    if type(chemin_fichier)!=str or os.path.isfile(chemin_fichier) == False:
        return 'text/html; charset=utf-8'
    res=mimetypes.guess_type(chemin_fichier)
    type_fichier , encodage = res
    if encodage==None:
        retour = type_fichier + '; charset=None'
    else: 
        retour = type_fichier + '; ' + encodage
    return retour

def main():
    config_srv.lire_configuration()
    time1=time.localtime()
    """
    Ici le main nous sert pour effectuer nos tests unitaires :
        Pour la fonction verifie_requete :
        3 correct : Requete classique
                    Requete avec une minuscule en premiere lettre
                    Requete avec des caractère spéciaux (è_œ^*$ etc...)
        5 incorrect : Requete avec une mauvaise déclaration GET
                      Requete avec une mauvaise déclaration d'HTTP
                      Requete avec sans ':'
                      Requete avec un caractère special au mauvaise endroit.
                      Requete avec seulement 2 champs dans la premiere ligne.
        
        Pour la fonction genere_entete: 
                Une réponse avec un code http erroné(201) et sans longueur
                Une reponse avec un code 200 et avec une longueur
                Une reponse acex un code 400 et avec une longueur
        
        Pour la fonction construit_chemin_fichier : 
                Un chemin avec seulement '/'
                Un chemin contenant un '?'
                Un chemin contenat des %nn etc... et finissant par '/'
                Un chemin contenat des %nn etc...
                Un chemin avec le nom du fichier correctement spécifier (/page_principal)
                
        Pour la fonction lecture_donnees : 
            Un chemin de fichier existant
            Un chemin de fichier inexistant
            Un chemin de fichier non lisible
            Un chemin de fichier qui est un int (5)
    """
    
    
    req1='''GET /index.html HTTP/1.1\r\nHost: localhost:8017\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\n

'''
#Bonne requete 
    
    req2='''GEt /index.html HTTP/1.1\r\nHost: localhost:8017\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
#requete avec une minuscule dans 'GEt'
    
    
    req3='''GET /index.html HTTP/\r\nHost: localhost:8017\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
#requete avec une mauvaise déclaration d'HTTP
    
    req4='''GET /index.html HTTP/1.1\r\nhost: localhost:8017\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
#requete avec une ligne ne commençant pas par une majuscule (host au lieu de Host)
    
    req5='''GET /index.html HTTP/1.1\r\nHost: localhost:8017\r\nUser-Agent Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
#requete qui ne contient pas de ':' (User-Agent Mozilla au lieu de User-Agent: Mozilla)
    
    req6='''GET /index.html HTTP/1.1\r\nH+st: localhost:8017\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
#requete avec un caractere special dans le permier champs (H+st au lieu de Host)a
    
    req7='''GET /index.html HTTP/1.1\r\nHost: localhost:8017é&œ(-è_çà))=+°Œ#~{[|`\^^@]}]}^$*ù£µ%¨§/\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''
    req8='''GET HTTP/1.1\r\nHost: localhost:8017é&œ(-è_çà))=+°Œ#~{[|`\^^@]}]}^$*ù£µ%¨§/\r\nUser-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0\r\nAccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1

'''

#requete avec un grand nombre de caractere speciaux dans la 2eme ligne
            

    
    assert verifie_requete(req1)==200
    print('req1 : ok')

    assert verifie_requete(req2)==405
    print('req2 : ok')
    
    assert verifie_requete(req3)==500
    print('req3 : ok')
    
    assert verifie_requete(req4)==200
    print('req4 : ok')
    
    assert verifie_requete(req5)==400
    print('req5 : ok')
    
    assert verifie_requete(req6)==400
    print('req6 : ok')

    assert verifie_requete(req7)==200
    print('req7 : ok')
    
    assert verifie_requete(req8)==400
    print('req8 : ok')
    
    
    #Test unitaire pour la fonction genere_entete
    reponse1='HTTP/1.1 500 INTERNAL SERVER ERROR\r\nDate: ' + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])   + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'

    reponse2='HTTP/1.1 200 OK\r\nDate: '  + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Length: 200\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
    
    reponse3='HTTP/1.1 400 BAD REQUEST\r\nDate: '  + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) +'\r\nServer: server_icard\r\nConnection: close\r\nContent-Length: 200\r\nContent-Type: text/html; charset=utf-8\r\n\r\n'
    
    assert genere_entete(400,200, 'text/html; charset=utf-8') == reponse3
    print ("Test avec le code 400 et une taille d'entete : ok")

    assert genere_entete(200,200, 'text/html; charset=utf-8') == reponse2
    print("Test avec le code 200 et une taille d'entete : ok")

    assert genere_entete(201,None, 'text/html; charset=utf-8') == reponse1
    print ('Test avec code 201 & taille=None : ok')
    
    
    #Test unitaire pour la fonction construit_chemin_fichier
    ligne = 'GET / HTTP/1.1'
    assert construit_chemin_fichier(ligne) == '/home/icard/src/M2207/Projet_tp_server/Site/index.html'
    print("Test chemin '/' : OK")
    
    ligne1 = 'GET /actuel/news.html?ordre=1 HTTP/1.1'
    assert construit_chemin_fichier(ligne1) == config_srv.get_config('rep_servi') + '/actuel/news.html'
    print("Test chemin '/actuel/news.html?ordre=1' : OK")
    
    ligne2 = 'GET /doc/doc%20en%20fran%C3%A7ais/ HTTP/1.1'
    assert construit_chemin_fichier(ligne2) == config_srv.get_config('rep_servi') + '/doc/doc en français/index.html'
    print("Test chemin '/doc/doc%20en%20fran%C3%A7ais/' : OK")

    ligne3 = 'GET /doc/doc%20en%20fran%C3%A7ais HTTP/1.1'
    assert construit_chemin_fichier(ligne3) == config_srv.get_config('rep_servi') + '/doc/doc en français'
    print("Test chemin '/doc/doc%20en%20fran%C3%A7ais' : OK")
    
    ligne4 = 'GET /page_principal HTTP/1.1'
    assert construit_chemin_fichier(ligne4) == config_srv.get_config('rep_servi') + '/page_principal'
    print("Test chemin '/page_principal' : OK")


    #Test unitaire pour la fonction lecture_donnees
    test = ('HTTP/1.1 200 OK\r\nDate: ' + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Length: 43\r\nContent-Type: text/plain; charset=None\r\n\r\n', b'\xef\xbb\xbfBonjour voici un fichier qui fonctionne\n')
    assert (lecture_donnees(config_srv.get_config('rep_servi')+'/classe_virtuelle.txt')) == test
    print('Test : fichier existant : OK')
    
    test1 = ('HTTP/1.1 404 NOT FOUND\r\nDate: ' + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Type: text/html; charset=utf-8\r\n\r\n', b'<html><body><center><h1>Error 404: NOT FOUND</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>')
    assert lecture_donnees(config_srv.get_config('rep_servi')+'/fichier_inexistant') == test1
    print('Test : fichier inexistant : OK')
    
    #test2 = ('HTTP/1.1 500 INTERNAL SERVER ERROR\r\nDate: ' + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Type: text/html; charset=utf-8\r\n\r\n', b'<html><body><center><h1>Error 500: INTERNAL SERVER ERROR</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>')
    #assert lecture_donnees(config_srv.get_config('rep_servi') + '/fichier_illisible.txt') == test2
    #print('Test : fichier illisible : OK')
    
    test3 = ('HTTP/1.1 404 NOT FOUND\r\nDate: ' + time.strftime('%A',time1) + ',' + ' ' + time.strftime('%d',time1)  + ' ' + time.strftime('%b',time1)  + ' ' +  str(time1[0])  + ' ' + str(time1[3])  + ':' + str(time1[4])  + ':' + str(time1[5]) + '\r\nServer: server_icard\r\nConnection: close\r\nContent-Type: text/html; charset=utf-8\r\n\r\n', b'<html><body><center><h1>Error 404: NOT FOUND</h1></center><p>Head back to <a href="/">home page</a>.</p></body></html>')
    assert lecture_donnees(5) == test3
    print('Test : avec un int en chemin de fichier : OK')
    
    
    #Test unitaire pour la fonction type_contenue
    fichier_existant = config_srv.get_config('rep_servi') + '/css/cv.css'
    assert type_contenu(fichier_existant) == 'text/css; charset=None'
    print('Test : type_contenue avec fichier existant : OK')
    
    fichier_inexistant = config_srv.get_config('rep_servi') + '/css/cv'
    assert type_contenu(fichier_inexistant) == 'text/html; charset=utf-8'
    print('Test : type_contenue avec fichier inexistant : OK')
    
    chemin_int =15
    assert type_contenu(chemin_int) == 'text/html; charset=utf-8'
    print("Test : type_contenue avec un chemin de fichier qui n'est pas une str : OK")

    
    
if __name__ == "__main__":
    main()
    

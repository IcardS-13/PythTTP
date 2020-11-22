#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 21 14:04:11 2020

@author: ICARD
"""
#module systeme :
import os.path
import os
import threading
import configparser
Config = configparser.ConfigParser()
verrou = threading.Lock()

def creer_config_defaut():
    '''
    Ici dans la fonction creer_config_defaut On va crée un fichier de configuration du serveur (un fichier INI)
    D'abord on verouille le cadena pour etre sur d'etre seul à travail sur le fichier.
    Ensuite on utilise l'objet 'Config' initialisé au dessus : Config = configparser.ConfigParser() pour stocker la configuration.
    on créer le fichier : .serveur-http.conf et ont ecrit l'objet Config dedans qui contient la configuration du serveur.
    Si j'amais on attrape un erreur on renvoie false pour prevenir que l'ecriture c'est mal déroulé.
    Sinon on relache le verrou et on return True.
    
    '''
    #verouillage du verrou
    verrou.acquire()
    try:
        #Config du serveur
        Config['global'] = {
                            'Hote': '',
                            'Port': '8000', 
                            'Rep_servi':os.path.join(os.environ['HOME'],"src", "M2207", "Projet_tp_server", 'Site')
                            }
        #Ecriture dans le fichier INI
        with open('.serveur-http.conf', 'w') as configfile:
            Config.write(configfile) 
    except OSError:
        return False
    
    #déverouillage du verrou
    verrou.release()
    return True


def lire_configuration():
    '''
    Dans la fonction lire_configuration on va lire le fichier de configuration (fichier ini) crée avec la fonction creer_config_defaut
    D'abord on verifie si le fichier existe sinon on le crée et on verifie que la création c'est bien déroulé.
    Ensuite on verouille le cadena, on lit le fichier .serveur-http.conf
    On récupere toutes les options et on les stocks dans la list 'clé'
    Apres on récupere les valeurs associée au clé dans la boucle for.
    On s'assure juste de transformer le numero de port en entier (int) avec la methode Config.getint.
    Et enfin on fait appele à la fonction set_config pour écrire dans le dictionnaire CONFIGURATION.
    Si j'amais on attrape un erreur on renvoie false pour prevenir que la lecture c'est mal déroulé.
    Sinon on return True
    '''
    try:
         #Vérification de l'existance du fichier INI
        if os.path.isfile('.serveur-http.conf') == False:
            creer_config_defaut()
            if creer_config_defaut() == False:
                print ("problème d'écriture du fichier de configuration")
                return False
        
        #lecture du fichier
        verrou.acquire()
        Config.read('.serveur-http.conf')
        cle = Config.options('global')
        verrou.release()
        
        #écriture de la config dans le dictionnaire grace à la fonction set_config
        for i in range (0, len(cle)):
            verrou.acquire()
            valeur = Config.get('global',cle[i])
            
            #changement du type du port (de str en int)
            try : 
                if i == 1:
                    valeur = Config.getint('global','Port')
            except Exception:
                cle[i]='Port'
                valeur=80
                
            verrou.release()
            set_config(cle[i],valeur)
            
        
    except OSError : 
        return False
    
    return True
    
CONFIGURATION = {}

CODE_ETAT={
         200 : "OK",
         400 : "BAD REQUEST",
         404 : "NOT FOUND",
         405 : "METHOD NOT ALLOWED",
         500 : "INTERNAL SERVER ERROR"
        }

PAGE_HTML_ERREUR={

        404 : b'''<html><body><center><h1>Error 404: NOT FOUND</h1></center><p>Head back to <a href=\"/\">home page</a>.</p></body></html>''',
        400 : b'''<html><body><center><h1>Error 400: BAD REQUEST</h1></center><p>Head back to <a href=\"/\">home page</a>.</p></body></html>''',
        405 : b'''<html><body><center><h1>Error 405: METHOD NOT ALLOWED</h1></center><p>Head back to <a href=\"/\">home page</a>.</p></body></html>''',
        500 : b'''<html><body><center><h1>Error 500: INTERNAL SERVER ERROR</h1></center><p>Head back to <a href=\"/\">home page</a>.</p></body></html>'''
        }


def get_config (cle) : 

    verrou.acquire()
    valeur = CONFIGURATION[cle]
    verrou.release()
    
    return valeur

def set_config (cle, valeur) : 
    verrou.acquire()
    CONFIGURATION[cle] = valeur
    verrou.release()
    


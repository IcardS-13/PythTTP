#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ce module est le coeur même du serveur c'est le programme principal qui fait tourner le serveur.
Il fait appel à different modules et differentes fonctions permettant de gerer les erreurs ou verifier le type de requete.

Created on Fri Feb 21 14:04:11 2020
@author: ICARD
"""
#modules systeme:
import socket
import threading
#modules interne:
import config_srv
import client_http
    
def server_stop(sock):
    """
    la fonction server_stop permet d'arreter le serveur.
    Elle est appelée en cas d'erreur sur le serveur.
    
    paramètre sock : correspond au socket utilisé par le serveur afin qu'il soit fermé.
    """
    print("Le serveur s'arrête") 
    sock.shutdown(socket.SHUT_RDWR) #arrêt 
    sock.close() #fermeture du socket



def ecoute(s):
    """
    la fonction ecoute permet d'ecouter sur le socket qui à été ouvert;
    paramètre s : correspond au socket utilisé par le serveur.
    """
    try:
        s.listen() #ecoute sur le socket
        while True:
            client,adr = s.accept() #connexion avec client
            print("connexion reçu de",adr)
            client_thread=threading.Thread(target=client_http.traite_client, args=(client,adr))
            client_thread.start()
    #gestion des erreurs possiblement crée par l'etablissement de la connexion avec le client
    except OSError: 
        server_stop(s)
        return
   
       
def main():
    """
    fonction principal qui permet de lancer le serveur.
    Elle gere l'ouverture du socket et communique les informations principales du serveur.
    """
    #recupération du dictionnaire appartenant au module config_srv contenant les infos principales du serveur
    ini = config_srv.lire_configuration()
    if ini == False :
        print('problème lors de la lecture ou création du fichier ini')
        return
    host='127.0.0.1'
    config_srv.set_config('hote',socket.gethostname())
    
    print("Nom d'hote :", config_srv.get_config('hote'))
    print("Numéro de Port :" , config_srv.get_config('port'))
    print("Réperetoire Servi :" , config_srv.get_config('rep_servi'))
    
    try:
        #ouverture du socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host,config_srv.get_config('port')))
            print("le serveur est démarré sur le port :",config_srv.get_config('port'))
            ecoute(sock) #appele de la fonction ecoute
            
    #gestion des erreurs
    except OSError:
        print("impossible d'ouvrir un socket sur ce port")
        server_stop(sock)
        return
    
    
if __name__ == "__main__":
    main()
    

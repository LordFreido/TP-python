import threading  # Permet de recevoir les messages en parallèle
import socket  # Permet de communiquer avec le serveur
import tkinter as tk  # Permet de créer l'interface graphique
from tkinter import messagebox  # Permet d'afficher les erreurs
from datetime import datetime  # Permet de récupérer l'heure actuelle
from queue import Queue, Empty  # Permet de transmettre les messages entre les threads


couleurs = {  # Associe une couleur à chaque utilisateur
    "Edan": "blue",  # Edan sera affiché en bleu
    "Antoine": "green"  # Antoine sera affiché en vert
}


class Client:  # Classe représentant un client du chat

    def __init__(self, username, server, port):  # Initialise le client
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Crée une socket TCP
        self.socket.connect((server, port))  # Se connecte au serveur
        self.username = username  # Enregistre le pseudo
        self.listening = True  # Active l'écoute
        self.send("USERNAME {0}".format(username))  # Envoie le pseudo au serveur

    def listener(self):  # Reçoit les messages du serveur
        while self.listening:  # Continue tant que le client est connecté
            try:  # Essaie de recevoir les données
                data = self.socket.recv(1024).decode("UTF-8")  # Reçoit le message
            except (socket.error, UnicodeDecodeError):  # Si une erreur se produit
                if self.listening:  # Vérifie que le client était connecté
                    messages_recus.put("Erreur : impossible de recevoir les données.")  # Ajoute l'erreur
                break  # Arrête l'écoute

            if data == "" or data == "QUIT":  # Si le serveur ferme la connexion
                break  # Arrête l'écoute

            self.handle_msg(data)  # Traite le message reçu

        self.tidy_up()  # Ferme la connexion
        messages_recus.put(None)  # Signale la déconnexion

    def listen(self):  # Démarre l'écoute des messages
        self.listen_thread = threading.Thread(target=self.listener, daemon=True)  # Crée le thread
        self.listen_thread.start()  # Démarre le thread

    def send(self, message):  # Envoie un message au serveur
        try:  # Essaie d'envoyer le message
            if not message.startswith("USERNAME "):  # Si ce n'est pas une identification
                message = "{0}: {1}".format(self.username, message)  # Ajoute le pseudo
            self.socket.sendall(message.encode("UTF-8"))  # Envoie le message
        except socket.error:  # Si l'envoi échoue
            messages_recus.put("Erreur : impossible d'envoyer le message.")  # Affiche l'erreur

    def tidy_up(self):  # Ferme la connexion
        self.listening = False  # Arrête l'écoute
        try:  # Essaie d'interrompre la socket
            self.socket.shutdown(socket.SHUT_RDWR)  # Interrompt la connexion
        except OSError:  # Si elle est déjà fermée
            pass  # Ignore l'erreur
        self.socket.close()  # Ferme la socket

    def handle_msg(self, data):  # Traite les messages reçus
        for ligne in data.splitlines():  # Parcourt les lignes reçues
            messages_recus.put(ligne)  # Ajoute le message à la file d'attente


def afficher_messages():  # Affiche les messages dans Tkinter
    try:  # Essaie de récupérer les messages
        while True:  # Parcourt les messages disponibles
            ligne = messages_recus.get_nowait()  # Récupère un message sans bloquer

            if ligne is None:  # Si le client est déconnecté
                entree_message.config(state="disabled")  # Désactive la saisie
                bouton_envoyer.config(state="disabled")  # Désactive le bouton
                ligne = "Connexion terminée."  # Prépare le message système

            pseudo = ligne.split(":", 1)[0].strip()  # Récupère le pseudo
            couleur = couleurs.get(pseudo, "orange")  # Choisit la couleur
            maintenant = datetime.now()  # Récupère la date et l'heure actuelles
            date_heure = f"{maintenant.day}/{maintenant.month}/{maintenant.year} {maintenant:%H:%M:%S}"  # Formate la date et l'heure

            zone_messages.config(state="normal")  # Autorise l'ajout de texte
            zone_messages.insert(tk.END, "[" + date_heure + "] " + ligne + "\n", couleur)  # Affiche la date, l'heure et le message
            zone_messages.config(state="disabled")  # Protège la zone
            zone_messages.see(tk.END)  # Descend au dernier message
    except Empty:  # Si aucun autre message n'est disponible
        pass  # Continue normalement

    fenetre.after(100, afficher_messages)  # Vérifie régulièrement les messages


def connexion():  # Connecte le client au serveur
    global client  # Rend le client accessible aux autres fonctions

    pseudo = entree_pseudo.get().strip()  # Récupère le pseudo
    serveur = entree_serveur.get().strip()  # Récupère l'adresse IP
    port_texte = entree_port.get().strip()  # Récupère le port

    if not pseudo:  # Vérifie les champs obligatoires
        messagebox.showwarning("Attention", "Veuillez remplir le Username.")  # Affiche un avertissement
        return  # Annule la connexion

    try:  # Essaie de se connecter
        client = Client(pseudo, serveur, int(port_texte))  # Crée le client
        client.listen()  # Lance la réception
        entree_pseudo.config(state="disabled")  # Bloque le pseudo
        entree_serveur.config(state="disabled")  # Bloque l'adresse IP
        entree_port.config(state="disabled")  # Bloque le port
        bouton_connexion.config(state="disabled")  # Désactive Connexion
        entree_message.config(state="normal")  # Active la saisie
        bouton_envoyer.config(state="normal")  # Active Envoyer
        messages_recus.put("Connexion réussie !")  # Confirme la connexion
    except OSError:  # Si la connexion échoue
        messagebox.showerror("Erreur", "Impossible de se connecter au serveur. Vérifiez l'IP du serveur, le port ")  # Affiche l'erreur


def envoyer():  # Envoie un message au serveur
    if client is None or not client.listening:  # Vérifie la connexion
        return  # Annule l'envoi

    message = entree_message.get().strip()  # Récupère le message

    if message:  # Vérifie que le message n'est pas vide
        if message == "QUIT":  # Si l'utilisateur veut quitter
            quitter()  # Appelle la fonction de fermeture
            return  # Arrête l'envoi
        else:  # Si c'est un message normal
            client.send(message)  # Envoie le message

        entree_message.delete(0, tk.END)  # Vide le champ


def quitter():  # Quitte proprement le chat
    if client is not None and client.listening:  # Vérifie si le client est connecté
        try:  # Essaie de prévenir le serveur
            client.socket.sendall(b"QUIT")  # Envoie la commande QUIT
        except OSError:  # Si la connexion est déjà fermée
            pass  # Ignore l'erreur
        client.tidy_up()  # Ferme la connexion

    fenetre.destroy()  # Ferme la fenêtre Tkinter


client = None  # Aucun client connecté au départ
messages_recus = Queue()  # Stocke les messages reçus entre les threads

fenetre = tk.Tk()  # Crée la fenêtre
fenetre.title("Chat Python")  # Définit le titre
fenetre.geometry("550x450")  # Définit la taille

cadre_connexion = tk.Frame(fenetre)  # Crée la zone de connexion
cadre_connexion.pack(pady=10)  # Place la zone en haut

tk.Label(cadre_connexion, text="Username :").grid(row=0, column=0, padx=5, pady=3)  # Affiche le label
entree_pseudo = tk.Entry(cadre_connexion, width=20)  # Crée le champ du pseudo
entree_pseudo.grid(row=0, column=1, padx=5, pady=3)  # Place le champ

tk.Label(cadre_connexion, text="Serveur :").grid(row=1, column=0, padx=5, pady=3)  # Affiche le label
entree_serveur = tk.Entry(cadre_connexion, width=20)  # Crée le champ du serveur
entree_serveur.insert(0, "127.0.0.1") # Le champ serveur est rempli
entree_serveur.grid(row=1, column=1, padx=5, pady=3)  # Place le champ

tk.Label(cadre_connexion, text="Port :").grid(row=2, column=0, padx=5, pady=3)  # Affiche le label
entree_port = tk.Entry(cadre_connexion, width=20)  # Crée le champ du port
entree_port.insert(0, "59001")
entree_port.grid(row=2, column=1, padx=5, pady=3)  # Place le champ

bouton_connexion = tk.Button(cadre_connexion, text="Connexion", command=connexion)  # Crée le bouton
bouton_connexion.grid(row=3, column=0, columnspan=2, pady=5)  # Place le bouton

zone_messages = tk.Text(fenetre, state="disabled", height=12)  # Crée la zone des messages
zone_messages.pack(fill="both", expand=True, padx=10, pady=5)  # Place la zone

zone_messages.tag_config("blue", foreground="blue")  # Configure le bleu
zone_messages.tag_config("green", foreground="green")  # Configure le vert
zone_messages.tag_config("orange", foreground="orange")  # Configure les messages système

cadre_envoi = tk.Frame(fenetre)  # Crée la zone d'envoi
cadre_envoi.pack(fill="x", padx=10, pady=10)  # Place la zone en bas

entree_message = tk.Entry(cadre_envoi, state="disabled")  # Crée le champ de message
entree_message.pack(side="left", fill="x", expand=True)  # Place le champ

bouton_envoyer = tk.Button(cadre_envoi, text="Envoyer", command=envoyer, state="disabled")  # Crée le bouton
bouton_envoyer.pack(side="left", padx=5)  # Place le bouton

entree_message.bind("<Return>", lambda evenement: envoyer())  # Envoie avec Entrée
fenetre.protocol("WM_DELETE_WINDOW", quitter)  # Ferme avec la croix
fenetre.after(100, afficher_messages)  # Lance l'affichage des messages
fenetre.mainloop()  # Démarre l'interface graphique

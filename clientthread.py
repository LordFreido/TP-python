from socket import socket
import threading 
import re 
import time
from better_profanity import profanity

class ClientListener(threading.Thread):

    def __init__(self, server, socket, address):
        super(ClientListener, self).__init__()
        self.server= server
        self.socket= socket
        self.address= address
        self.listening= True
        self.username= "No username"


    def run(self):
        while self.listening:
            data= ""
            try:
                data = self.socket.recv(1024).decode('UTF-8')
            except socket.error:
                print("Unable to receive data")
            self.handle_msg(data)
            time.sleep(0.1)
        print("Ending client thread for", self.address)
 
 
    def quit(self):
        self.listening = False
        self.socket.close()
        self.server.remove_socket(self.socket)
        self.server.echo("{0} has quit\n".format(self.username))

    def handle_msg(self, data):
        print(self.address, "sent :", data)
        username_result = re.search('^USERNAME (.*)$', data)
        if username_result:
            self.username = username_result.group(1)
            self.server.echo("{0} has joined.\n".format(self.username))
        elif data == "QUIT":
            self.quit()
        elif data == "":
            self.quit()
        else:
            # Indentation alignée exactement sous le 'elif'
            if profanity.contains_profanity(data):
                print(f"[MODERATION] Message de {self.username} ({self.address}) bloqué !") 
                try:
                    warning = "SERVEUR: Votre message contient des mots interdits et n'a pas été envoyé.\n"
                    self.socket.sendall(warning.encode("UTF-8"))
                except socket.error:
                    pass
            else:
                self.server.echo(data)
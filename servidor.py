import socket
import threading
import sys
import time
from random import randint
#from random import *


#from PyQt5.QtCore import QObject, QThread, pyqtSignal

host = '127.0.0.1'
port = 55555

class Server():
    def __init__(self, host, port):
        self.tempoRodada = 0
        self.pontoPorAcerto = 1
        self.maxTempoRodada = 50
        self.partidaEmAndamento = False
        self.resposta = "null"
        self.dica = "null"
        self.tema = "null"
        self.ultimoMestre = "null"
        self.mestreDefine =  'null'
        self.countPartidas = 0
        self.host = host
        self.port = port
        self.clients = []
        self.apelidos = []
        self.pontos = []
        self.estaBloqueado = False
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.flags = []
        self.respostaEncriptada = ''

        self.iniciar()


    def broadcast(self, message):
        for client in self.clients:
            try:
                client.send(message)
            except:
                self.removerClient(client)

    def removerClient(self, client):
        try:
            index = self.clients.index(client)
            self.clients.remove(client)
            #self.apelidos.remove(self.apelidos[index])
            self.removerApelido(index)
            client.close()
        except:
            pass
    
    def removerApelido(self, index):
        try:
            if(self.apelidos[index]):
                ap = self.apelidos[index]
                self.pontos.pop(index)
                self.apelidos.remove(ap)
                self.broadcast(('!Ap-conectados,'+'*'.join(map(str, self.apelidos))).encode('utf-8'))
                time.sleep(0.05)
                self.broadcast(('!Ap-desconectado,{}'.format(ap)).encode('utf-8'))
        except:
            print(f'[Except: removerApelido({index})')

    def adicionarApelido(self, client, apelido):
        try:
            index = self.clients.index(client)
            #self.apelidos.append(apelido)
            #self.apelidos[index] = apelido
            self.apelidos.insert(index, apelido)
            client.send('!ap-aceito'.encode('utf-8'))
            time.sleep(0.05)
            self.broadcast(('!Ap-conectados,'+'*'.join(map(str, self.apelidos))).encode('utf-8'))
            self.pontos.insert(index, 0)
        except:
            print("[Except: adicionarApelido]")

    def escutar(self, client):
        while True:
                try:
                    message = client.recv(1024).decode('utf-8')
                    if(self.estaBloqueado==False):
                        #message_tuple = tuple(map(str, message.split('||')))
                        message_tuple = message.split(',')

                        if(message_tuple[0]=='!sair'):
                            client.send('!removido'.encode('utf-8'))
                            self.removerClient(client)
                            print('[Cliente desconectado]')
                            break
                        elif(message_tuple[0]=='!print'):
                            print('\n', message_tuple[1])
                        elif(message_tuple[0]=='!definir-apelido'):
                            print('[Apelido]')
                            if(message_tuple[1] in self.apelidos):
                                print('[Apelido já existe]')
                                time.sleep(0.005)
                                client.send('!apelido-ja-existe'.encode('utf-8'))
                                #removerClient(client)
                            else:
                                self.adicionarApelido(client, message_tuple[1])
                                print("cliente e apelido add: ", self.apelidos)
                        elif(message_tuple[0]=='!iniciar-partida'):
                            self.iniciarJogo()
                        elif(message_tuple[0]=='!resposta'):
                            if(message_tuple[1] == self.resposta):
                                index = self.clients.index(client)
                                self.broadcast('!print-log,acertou,{}'.format(self.apelidos[index]).encode('utf-8'))
                                #(self.pontos[index] + self.pontoPorAcerto*self.tempoRodada)
                                #self.pontos.insert(index, (self.pontos[index] + 10))
                                self.pontos[index] = (self.pontos[index] + self.pontoPorAcerto*self.tempoRodada)
                                indexMestre = self.apelidos.index(self.ultimoMestre)
                                #(self.tempoRodada*self.pontoPorAcerto)
                                #self.pontos.insert(indexMestre, (self.pontos[indexMestre] + 5))
                                self.pontos[indexMestre] = (self.pontos[indexMestre] + int(self.pontoPorAcerto*self.maxTempoRodada*(1/(len(self.apelidos)-1))))
                                print(indexMestre, '<---')
                                print(self.ultimoMestre, self.apelidos.index(self.ultimoMestre), self.apelidos[index])
                                print(self.pontos)
                                time.sleep(0.5)
                                self.atualizarPontos()
                            else:
                                self.broadcast('!print-log,{},{}'.format(message_tuple[1], "null").encode('utf-8'))
                        elif(message_tuple[0]=='!tema-escolhido'):
                            print('[tema-escolhido: ]', message_tuple[1])
                            self.temaEscolhido(message_tuple[1], message_tuple[2], message_tuple[3])
                            index = self.clients.index(client)
                            self.ultimoMestre = self.apelidos[index]
                        
                        elif(message_tuple[0]!=''): print("cliente: "+ str(message_tuple))

                    
                except:
                    self.removerClient(client)
                    break

    def atualizarTimeConexao(self):
        t = 10
        for i in range(t, 0, -1):
            value = (i*100)/t
            self.broadcast('!atualizarTimerConexao,{},{}'.format(int(value), i).encode('utf-8'))
            time.sleep(1)
            

    def iniciarJogo(self):
        threadTimer = threading.Thread(target=self.atualizarTimeConexao, args=())
        threadTimer.start()# Instanciando uma thread em paralelo à principal -> QAplication.


        
        threadTimer.join()
        #self.broadcast('!iniciar-partida'.encode('utf-8'))
        
        self.iniciarPartida()

    def atualizarPontos(self):
        self.broadcast(('!pontos,'+'*'.join(map(str, self.apelidos))+','+'*'.join(map(str, self.pontos))).encode('utf-8'))
        #print('!pontos,'+'*'.join(map(str, self.apelidos))+','+'*'.join(map(str, self.pontos)))

    def iniciarPartida(self):
        self.partidaEmAndamento = False
        if(len(self.apelidos)>0):
            index = randint(0,len(self.apelidos)-1)
            while(self.apelidos[index] == self.ultimoMestre or self.apelidos[index] == self.mestreDefine):
                index = randint(0,len(self.apelidos)-1)
            
            print('\nindex: ',index)
            #self.ultimoMestre = self.apelidos[index]
            self.mestreDefine = self.apelidos[index]
            self.broadcast('!definir-tema,{}'.format(self.apelidos[index]).encode('utf-8'))

            threadTimerDefinir = threading.Thread(target=self.atualizarTimeDefinirTema, args=())
            threadTimerDefinir.start()# Instanciando uma thread em paralelo à principal -> QAplication

            
            # threadTimerDefinir.join()
            # if(self.partidaEmAndamento == False): self.iniciarPartida()
    
    def revelarLetra(self):
        if(len(self.resposta)>1):
            p = randint(0, len(self.resposta)-1)
            while self.flags[p] == True:
                p = randint(0, len(self.resposta)-1)
            self.flags[p] = True

            print('[revelarLetra]')
            print(self.flags)
    
    def criarFlags(self):
        for i in range(0, len(self.resposta)):
            self.flags.append(False)
        
        print('[criarFlags]')
        print(self.flags)

    def encriptar(self):
        palavraEncriptada = ''
        for i in range(0, len(self.resposta)):
            if(self.flags[i] == True):
                palavraEncriptada = palavraEncriptada + self.resposta[i]+' '
            else:
                palavraEncriptada = palavraEncriptada + '_ '
        return palavraEncriptada
        
    def atualizarTimeDefinirTema(self):
        t = 15
        for i in range(t, 0, -1):
            if(self.partidaEmAndamento == True): break
            value = (i*100)/t
            self.broadcast('!atualizarTimerDefinirTema,{},{}'.format(int(value), i).encode('utf-8'))
            time.sleep(1)

        #testando   
        if(self.partidaEmAndamento == False): self.iniciarPartida()
            
    def temaEscolhido(self, tema, dica, resposta):
        self.partidaEmAndamento = True
        self.tema = tema
        self.dica = dica
        self.resposta = resposta
        self.ultimoMestre = self.mestreDefine
        
        print(f"tema: {self.tema},{self.dica},{self.resposta}\n")
        self.broadcast('!iniciar-partida,{}'.format(self.ultimoMestre).encode('utf-8'))
        threadTimerDefinir = threading.Thread(target=self.atualizarTimePartida, args=())
        threadTimerDefinir.start()# Instanciando uma thread em paralelo à principal -> QAplication.


        # threadTimerDefinir.join()
        # if(self.partidaEmAndamento == True): 
        #     self.partidaEmAndamento = False
        #     self.encerrarPartida()
        #     self.iniciarPartida()
    
    def encerrarPartida(self):
        self.broadcast('!reset-tela-jogo'.encode('utf-8'))

    

    def atualizarTimePartida(self):
        self.atualizarPontos()
        contador = 0
        limite = int(len(self.resposta)*0.5)
        self.flags = []
        self.criarFlags()
        t = self.maxTempoRodada
        self.broadcast('!setar-tema,{},{},{}'.format(self.tema, self.dica, self.encriptar()).encode('utf-8'))
        time.sleep(0.1)
        for i in range(t, 0, -1):
            self.tempoRodada = i
            if(self.partidaEmAndamento == False): break
            value = (i*100)/t
            self.broadcast('!atualizarTimerPartida,{},{}'.format(int(value), i).encode('utf-8'))
            time.sleep(0.5)
            if(i%5 == 0 and contador < limite):
                self.revelarLetra()
                self.broadcast('!setar-tema,{},{},{}'.format(self.tema, self.dica, self.encriptar()).encode('utf-8'))
                contador+=1
            time.sleep(0.5)

        time.sleep(0.5)
        
        #testando
        if(self.partidaEmAndamento == True): 
            self.partidaEmAndamento = False
            self.encerrarPartida()
            time.sleep(0.5)
            self.iniciarPartida()


    def entrada(self):
        global estaBloqueado
        while True:
            entrada = str(input('>: '))
            #entrada_tuple = tuple(map(str, entrada.split('||')))
            entrada_tuple = entrada.split(',')
            #removedorAspas = slice(1, -1)
            if(entrada_tuple[0]=='!bloquear'):
                self.estaBloqueado = True
            elif(entrada_tuple[0]=='!desbloquear'):
                self.estaBloqueado = False
            elif(entrada_tuple[0] == '*print-clients'): print("\n-- ", self.clients)
            elif(entrada_tuple[0] == '*print-apelidos'): print("\n-- ", self.apelidos, len(self.apelidos))
            else:   self.broadcast(str(entrada).encode('utf-8'))

    def iniciar(self):
        self.server.bind((self.host, int(self.port)))
        self.server.listen()
        self.threadEnviar = threading.Thread(target=self.entrada, args=())
        self.threadEnviar.start()
        while True:
            client, address = self.server.accept()
            if(self.estaBloqueado==False):
                print("Conectado com {}".format(str(address)))

                self.clients.append(client)

                client.send('!conectado'.encode('utf-8'))
                time.sleep(0.05)

                threadEscuta = threading.Thread(target=self.escutar, args=(client,))
                
                threadEscuta.start()



if len(sys.argv) != 3:
    print("use:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1:3]
server = Server(host, port)
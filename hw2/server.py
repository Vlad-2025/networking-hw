import socket

HOST        = '127.0.0.1'
PORT        = 9999
BUFFER_SIZE = 1024

clienti_conectati = {}

mesaje: dict[int, tuple[str, str]] = {}
id_mesaj = 0 # incrementat cu 1 la fiecare mesaj

def adauga_mesaj(adresa_client:str, mesaj: str, ) -> int:
    global id_mesaj, mesaje
    mesaje[id_mesaj] = (adresa_client, mesaj)

    id_curent = id_mesaj
    id_mesaj += 1

    return id_curent

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print("=" * 50)
print(f"  SERVER UDP pornit pe {HOST}:{PORT}")
print("  Asteptam mesaje de la clienti...")
print("=" * 50)

while True:
    try:
        date_brute, adresa_client = server_socket.recvfrom(BUFFER_SIZE)
        mesaj_primit = date_brute.decode('utf-8').strip()

        parti = mesaj_primit.split(' ', 1)
        comanda = parti[0].upper()
        argumente = parti[1] if len(parti) > 1 else ''

        print(f"\n[PRIMIT] De la {adresa_client}: '{mesaj_primit}'")

        if comanda == 'CONNECT':
            if adresa_client in clienti_conectati:
                raspuns = "EROARE: Esti deja conectat la server."
            else:
                clienti_conectati[adresa_client] = True
                nr_clienti = len(clienti_conectati)
                raspuns = f"OK: Conectat cu succes. Clienti activi: {nr_clienti}"
                print(f"[SERVER] Client nou conectat: {adresa_client}")

        elif comanda == 'DISCONNECT':
            if adresa_client in clienti_conectati:
                del clienti_conectati[adresa_client]
                raspuns = "OK: Deconectat cu succes. La revedere!"
                print(f"[SERVER] Client deconectat: {adresa_client}")
            else:
                raspuns = "EROARE: Nu esti conectat la server."

        elif comanda == 'PUBLISH':
            if adresa_client in clienti_conectati:
                if argumente:
                    # salvare mesaj
                    id_returnat = adauga_mesaj(adresa_client, argumente)
                    raspuns = f"OK: mesaj trimis cu ID-ul {id_returnat}"

                    for client in clienti_conectati:
                        if client != adresa_client:
                            notificare = f"[MESAJ NOU]: {adresa_client}#{id_returnat}: {argumente}"
                            server_socket.sendto(notificare.encode('utf-8'), client)

                else:
                    raspuns = "EROARE: comanda PUBLISH necesita parameterii"
            else:
                raspuns = "EROARE: Nu sunteti conectat"

        elif comanda == 'DELETE':
            if adresa_client in clienti_conectati:
                try:
                    id_de_sters = int(argumente)
                except ValueError:
                    raspuns = "EROARE: ID-ul trebuie sa fie un numar intreg"
                else:
                    if id_de_sters in mesaje:
                        autor, text = mesaje[id_de_sters]

                        if autor == adresa_client:
                            del mesaje[id_de_sters]
                            raspuns = f"OK: mesajul {text} cu ID-ul {id_de_sters} a fost sters"
                        else:
                            raspuns = "EROARE: nu sunteti autorul acestui mesaj"
                    else:
                        raspuns = f"EROARE: mesajul cu ID-ul {id_de_sters} nu a fost gasit"
            else:
                raspuns = "EROARE: nu sunteti conectat"

        elif comanda == 'LIST':
            if adresa_client in clienti_conectati:
                lista_mesaje: list = []

                for id_sender, (autor, text) in mesaje.items():
                    if autor == adresa_client:
                        lista_mesaje.append((id_sender, text))

                raspuns = str(lista_mesaje)

            else:
                raspuns = "EROARE: nu sunteti conectat"

        else:
            raspuns = f"EROARE: Comanda '{comanda}' este necunoscuta. Comenzi valide: CONNECT, DISCONNECT, PUBLISH, DELETE, LIST"

        server_socket.sendto(raspuns.encode('utf-8'), adresa_client)
        print(f"[TRIMIS]  Catre {adresa_client}: '{raspuns}'")

    except KeyboardInterrupt:
        print("\n[SERVER] Oprire server...")
        break
    except Exception as e:
        print(f"[EROARE] {e}")

server_socket.close()
print("[SERVER] Socket inchis.")

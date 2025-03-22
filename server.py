import socket
import threading
import hashlib
import os

HOST = '127.0.0.1'   # ou 0.0.0.0 para aceitar de qualquer interface
PORT = 5000
FILENAME = 'arquivo.txt'

# Lista para armazenar os sockets dos clientes conectados
clients = []
clients_lock = threading.Lock()

def compute_hash(data):
    """Calcula o hash SHA256 dos dados fornecidos."""
    return hashlib.sha256(data).hexdigest()

def broadcast_file(file_data):
    """Envia a versão atualizada do arquivo para todos os clientes conectados."""
    file_hash = compute_hash(file_data)
    with clients_lock:
        for client in clients:
            try:
                # Notifica que há um novo arquivo disponível
                client.sendall("NEWFILE".encode())
                # Envia o tamanho do arquivo seguido de uma quebra de linha para separar
                client.sendall((str(len(file_data)) + "\n").encode())
                # Envia o conteúdo do arquivo
                client.sendall(file_data)
                # Envia o hash calculado
                client.sendall(file_hash.encode())
            except Exception as e:
                print("Erro ao enviar para o cliente:", e)

def handle_client(conn, addr):
    print("Cliente conectado:", addr)
    with conn:
        while True:
            try:
                # Recebe o comando (REQUEST ou UPDATE)
                data = conn.recv(1024).decode().strip()
                if not data:
                    break
                print(f"Recebido do {addr}: {data}")

                if data == "REQUEST":
                    # Cliente solicitou o arquivo
                    if os.path.exists(FILENAME):
                        with open(FILENAME, "rb") as f:
                            file_data = f.read()
                        # Informa que o arquivo foi encontrado
                        conn.sendall("FOUND".encode())
                        # Envia o tamanho do arquivo (com um \n para facilitar a separação)
                        conn.sendall((str(len(file_data)) + "\n").encode())
                        # Envia o conteúdo do arquivo
                        conn.sendall(file_data)
                        # Calcula e envia o hash do arquivo
                        file_hash = compute_hash(file_data)
                        conn.sendall(file_hash.encode())
                    else:
                        conn.sendall("NOTFOUND".encode())

                elif data == "UPDATE":
                    # Recebe o tamanho do arquivo (até a quebra de linha) e possivelmente parte do conteúdo
                    size_data = ""
                    while "\n" not in size_data:
                        size_data += conn.recv(1024).decode()
                    # Divide a string no primeiro '\n'
                    size_line, remainder = size_data.split("\n", 1)
                    try:
                        file_size = int(size_line.strip())
                    except ValueError:
                        print(f"Erro: tamanho inválido recebido: {size_line}")
                        continue

                    # A parte restante já recebida pode ser parte do conteúdo do arquivo
                    file_data = remainder.encode()
                    # Continua recebendo dados até atingir file_size bytes
                    while len(file_data) < file_size:
                        chunk = conn.recv(1024)
                        if not chunk:
                            break
                        file_data += chunk

                    # Calcula o hash da nova versão
                    new_hash = compute_hash(file_data)
                    
                    # Atualiza o arquivo no servidor
                    with open(FILENAME, "wb") as f:
                        f.write(file_data)
                    print(f"Arquivo atualizado por {addr}. Novo hash: {new_hash}")
                    
                    # Notifica todos os clientes com a nova versão do arquivo
                    broadcast_file(file_data)

                else:
                    conn.sendall("COMANDO INVÁLIDO".encode())
            except Exception as e:
                print(f"Erro com o cliente {addr}: {e}")
                break
    with clients_lock:
        if conn in clients:
            clients.remove(conn)
    print("Cliente desconectado:", addr)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Servidor ouvindo em {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            with clients_lock:
                clients.append(conn)
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
    except KeyboardInterrupt:
        print("Servidor encerrando...")
    finally:
        server.close()

if __name__ == "__main__":
    main()

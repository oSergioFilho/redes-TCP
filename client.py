import socket
import threading

HOST = '127.0.0.1'
PORT = 5000
FILENAME = 'arquivo.txt'

def receive_messages(sock):
    """Thread que fica ouvindo mensagens do servidor."""
    while True:
        try:
            data = sock.recv(1024).decode().strip()
            if not data:
                break

            if data == "FOUND":
                # Recebe o tamanho do arquivo
                size_str = ""
                while "\n" not in size_str:
                    size_str += sock.recv(1024).decode()
                file_size = int(size_str.strip())
                # Recebe o conteúdo do arquivo
                file_data = b""
                while len(file_data) < file_size:
                    file_data += sock.recv(1024)
                # Recebe o hash do arquivo
                file_hash = sock.recv(1024).decode().strip()
                # Salva o arquivo recebido
                with open(FILENAME, "wb") as f:
                    f.write(file_data)
                print(f"\n[INFO] Arquivo recebido. Hash: {file_hash}\n")

            elif data == "NEWFILE":
                # Recebe o tamanho do arquivo atualizado
                size_str = ""
                while "\n" not in size_str:
                    size_str += sock.recv(1024).decode()
                file_size = int(size_str.strip())
                # Recebe o conteúdo do arquivo atualizado
                file_data = b""
                while len(file_data) < file_size:
                    file_data += sock.recv(1024)
                # Recebe o hash do arquivo atualizado
                file_hash = sock.recv(1024).decode().strip()
                # Salva o arquivo atualizado
                with open(FILENAME, "wb") as f:
                    f.write(file_data)
                print(f"\n[INFO] Arquivo atualizado recebido. Hash: {file_hash}\n")
            else:
                print("\n[Mensagem do servidor]:", data)
        except Exception as e:
            print("\n[Erro ao receber mensagem]:", e)
            break

def show_menu():
    """Exibe o menu interativo."""
    print("\n===== MENU =====")
    print("1 - Solicitar arquivo (REQUEST)")
    print("2 - Atualizar arquivo (UPDATE)")
    print("0 - Sair")
    print("================\n")

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print("Conectado ao servidor.")

    # Inicia a thread que escuta mensagens do servidor
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    while True:
        show_menu()
        opcao = input("Selecione uma opção: ").strip()

        if opcao == '1':
            sock.sendall("REQUEST".encode())

        elif opcao == '2':
            try:
                with open(FILENAME, "rb") as f:
                    file_data = f.read()
                sock.sendall("UPDATE".encode())
                # Envia o tamanho do arquivo seguido de uma quebra de linha para separar
                sock.sendall((str(len(file_data)) + "\n").encode())
                # Envia o conteúdo do arquivo
                sock.sendall(file_data)
                print("\n[INFO] Atualização enviada ao servidor.")
            except FileNotFoundError:
                print("\n[ERRO] Arquivo não encontrado localmente. Faça um REQUEST primeiro ou crie o arquivo.")

        elif opcao == '0':
            print("\nEncerrando o cliente.")
            sock.close()
            break

        else:
            print("\n[ERRO] Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()

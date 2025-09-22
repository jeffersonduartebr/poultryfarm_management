import getpass
from user_management import create_initial_user, get_engine
from db import init_db

def main():
    print("--- Assistente de Criação de Usuário Administrador ---")
    
    engine = get_engine()
    init_db(engine)
    
    try:
        username = input("Digite o nome de usuário para o novo administrador: ")
        password = getpass.getpass("Digite a senha: ")
        password_confirm = getpass.getpass("Confirme a senha: ")

        if password != password_confirm:
            print("\nAs senhas não coincidem. Operação cancelada.")
            return

        if not username or not password:
            print("\nNome de usuário e senha não podem estar vazios. Operação cancelada.")
            return
            
        create_initial_user(username, password)
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")

if __name__ == '__main__':
    main()
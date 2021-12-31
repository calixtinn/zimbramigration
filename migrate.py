# -*- coding: utf-8 -*-
from os import system, path, listdir
from subprocess import getoutput, getstatusoutput


# @author: Matheus Calixto

def main():
    opcao = menu()
    domain = get_domain(opcao)
    if opcao == '1':
        export_domain(domain)
        return 0
    import_domain(domain)
    return 0


def get_account_passwords(domain_accounts, domain):
    for user in domain_accounts:
        system('su - zimbra -c \'zmprov -l ga ' + user + ' userPassword | grep userPassword: | awk "{ print $2 }" > '
               + migrations_dir + '/' + domain + '/passwords/' + user + '.shadow\'')


def get_account_details(domain_accounts, domain):
    for user in domain_accounts:
        system('su - zimbra -c \'zmprov ga ' + user + '  | grep -i Name: > '
               + migrations_dir + '/' + domain + '/account-details/' + user + '.txt\'')


def get_distribution_lists(domain):
    system('su - zimbra -c \'zmprov gadl | grep ' + domain + ' > ' + migrations_dir + '/' + domain
           + '/distribution_lists/distribution_lists.txt\'')

    system('su - zimbra -c \'for list in `cat ' + migrations_dir + '/' + domain
           + '/distribution_lists/distribution_lists.txt' + '`; do zmprov gdlm $list > ' + migrations_dir + '/' + domain
           + '/distribution_lists/$list.txt; done\'')


def get_account_aliases(domain_accounts, domain):
    for user in domain_accounts:
        system('su - zimbra -c \'zmprov ga ' + user + ' | grep zimbraMailAlias | sed "s/zimbraMailAlias: //g" > '
               + migrations_dir + '/' + domain + '/aliases/' + user + '.txt\'')

    system('find ' + migrations_dir + '/' + domain + '/aliases/ -type f -empty | xargs -n1 rm -v '
                                                     ' &> /dev/null')


def get_account_mailbox(domain_accounts, domain):
    for user in domain_accounts:
        system('su - zimbra -c \'zmmailbox -z -m ' + user + ' getRestURL \'//?fmt=tgz\' > '
               + migrations_dir + '/' + domain + '/mailbox_data/' + user + '.tar.gz\'')


def get_account_filters(domain_accounts, domain):
    for user in domain_accounts:
        system('su - zimbra -c \'zmprov ga ' + user + ' zimbraMailSieveScript > /tmp/' + user + '\'')
        system('sed -i -e "1d" /tmp/' + user)
        system('sed \'s/zimbraMailSieveScript: //g\' /tmp/' + user + ' > ' + migrations_dir + '/'
               + domain + '/filters/' + user + ';')
        system('rm /tmp/' + user)

    system('find ' + migrations_dir + '/' + domain + '/filters/ -type f -empty | xargs -n1 rm -v '
                                                     ' &> /dev/null')


def get_domain_accounts(domain):
    accounts = getoutput('su - zimbra -c \'zmprov -l gaa ' + domain +
                         ' | grep -vE "ham\.|quarantine|galsync|spam\.|admin"\'').split('\n')
    for account in accounts:
        system('touch ' + migrations_dir + '/' + domain + '/accounts/' + account + '.txt')
    return accounts


def compress_dir(domain):
    system('tar czvf /tmp/migracao-' + domain + '.tar.gz -C ' + migrations_dir + '/'
           + domain + ' ./')
    print("\n\n[!] Exportação concluída! Arquivo compactado: /tmp/migracao-" + domain + ".tar.gz")


def create_dir(domain):
    domain_dir = migrations_dir + '/' + domain
    account_dir = domain_dir + '/accounts'
    account_details = domain_dir + '/account-details'
    account_passwords = domain_dir + '/passwords'
    account_distribution_lists = domain_dir + '/distribution_lists'
    account_aliases = domain_dir + '/aliases'
    account_mailbox = domain_dir + '/mailbox_data'
    account_filters = domain_dir + '/filters'

    for folder in [domain_dir, account_dir, account_details, account_passwords, account_distribution_lists,
                   account_aliases, account_mailbox, account_filters]:
        system('mkdir -p ' + folder)

    system('chmod -R 777 ' + migrations_dir)


def export_domain(domain):
    print("[+] Exportação iniciada!\n")
    create_dir(domain)
    print("[+] Obtendo contas do domínio...\n")
    domain_accounts = get_domain_accounts(domain)
    print("[+] Exportando detalhes das contas...\n")
    get_account_details(domain_accounts, domain)
    print("[+] Exportando senhas das contas...\n")
    get_account_passwords(domain_accounts, domain)
    print("[+] Exportando listas de distribuição...\n")
    get_distribution_lists(domain)
    print("[+] Exportando aliases das contas...\n")
    get_account_aliases(domain_accounts, domain)
    print("[+] Exportando caixas de e-mails das contas...\n")
    get_account_mailbox(domain_accounts, domain)
    print("[+] Exportando filtros das contas...\n")
    get_account_filters(domain_accounts, domain)
    print("[+] Compactando Diretório...")
    compress_dir(domain)


def create_domain(domain):
    print("\n[+] Criando domínio: " + domain)
    system('su - zimbra -c \'zmprov cd ' + domain + ' zimbraAuthMech zimbra\'')


def restore_accounts(domain):
    print("\n[+] Restaurando contas...")
    accounts = listdir(migrations_dir + '/' + domain + '/accounts/')
    for account in accounts:
        account_name = account.replace('.txt', '')
        print("\n[.] Criando conta: " + account_name)
        given_name = \
            getoutput('grep givenName: ' + migrations_dir + '/' + domain + '/account-details/' + account +
                      ' | cut -d ":" -f2').strip()
        display_name = \
            getoutput('grep displayName: ' + migrations_dir + '/' + domain + '/account-details/' + account +
                      ' | cut -d ":" -f2').strip()
        shadow_pass = \
            getoutput('cat ' + migrations_dir + '/' + domain + '/passwords/' + account_name + '.shadow '
                                                                                              '| cut -d ":" -f2').strip()
        system('su - zimbra -c \'' + zimbra_language + ' zmprov ca ' + account_name + ' "TeMpPa55^()" cn "' + given_name +
               '" displayName "' + display_name + '" givenName "' + given_name + '"\'')
        system('su - zimbra -c \'zmprov ma ' + account_name + ' userPassword "' + shadow_pass + '"\'')
    return accounts


def decompress_dir(domain):
    file = ''
    exists = False
    while not exists:
        file = input('[?] Digite o caminho completo do arquivo compactado:  ')
        exists = verify_compresses_file(file)
        if not exists:
            print("[X] Arquivo não encontrado!\n\n")
    print("[+] Descompactando arquivo no diretório: /tmp/migracoes/" + domain + "\n")
    system('mkdir -p /tmp/migracoes/' + domain)
    system('tar zxf ' + file + ' -C /tmp/migracoes/' + domain)
    system('chown -R zimbra:zimbra ' + migrations_dir)


def restore_distribution_list(domain):
    print("\n[+] Restaurando Listas de distribuição relacionadas ao domínio " + domain)
    distribution_lists = getoutput('cat ' + migrations_dir + '/' + domain +
                                   '/distribution_lists/distribution_lists.txt').split('\n')
    if len(distribution_lists) > 0 and distribution_lists[0] != '':
        for distr_list in distribution_lists:
            system('su - zimbra -c \'zmprov cdl ' + distr_list + '\'')
            members = getoutput('grep -v "#" ' + migrations_dir + '/' + domain + '/distribution_lists/'
                                + distr_list + '.txt | grep "@"').split('\n')
            for member in members:
                system('su - zimbra -c \'zmprov adlm ' + distr_list + ' ' + member + '\'')


def restore_aliases(domain, accounts):
    print("\n[+] Restaurando aliases... ")
    for user in accounts:
        account = user.replace('.txt', '')
        print("[.] Restaurando aliases da conta: " + account)
        user_alias = migrations_dir + '/' + domain + '/aliases/' + account + '.txt'
        if path.isfile(user_alias):
            aliases = getoutput('grep "@" ' + user_alias).split('\n')
            for alias in aliases:
                system('su - zimbra -c \'zmprov aaa ' + account + ' ' + alias + '\'')


def restore_mailboxes(domain, accounts):
    print("\n[+] Restaurando Mailboxes... ")
    for user in accounts:
        account = user.replace('.txt', '')
        print("[.] Restaurando mailbox da conta: " + account)
        system('su - zimbra -c \'zmmailbox -z -m ' + account + ' postRestURL "/?fmt=tgz&resolve=skip" '
               + migrations_dir + '/' + domain + '/mailbox_data/' + account + '.tar.gz' + '\'')


def restore_filters(domain, accounts):
    print("\n[+] Restaurando filtros... ")
    for user in accounts:
        account = user.replace('.txt', '')
        script = getoutput('cat ' + migrations_dir + '/' + domain + '/filters/' + account).strip()
        if len(script) > 0:
            system('su - zimbra -c \'zmprov ma ' + account +
                   ' zimbraMailSieveScript "`cat ' + migrations_dir + '/' + domain + '/filters/' + account + '`"\'')


def import_domain(domain):
    decompress_dir(domain)
    create_domain(domain)
    accounts = restore_accounts(domain)
    restore_distribution_list(domain)
    restore_aliases(domain, accounts)
    restore_mailboxes(domain, accounts)
    restore_filters(domain, accounts)
    print("\n\n[!] Importação concluída do Domínio: " + domain)


def get_domain(opcao):
    domain = ''
    invalido = True
    while invalido:
        domain = input('Digite o domínio para a migração: ')
        status = verify_domain(domain)
        if status != 0 and opcao == '1':
            print("[X] Domínio não encontrado!\n\n")
        elif opcao == '2' and status == 0:
            print("[X] Domínio já existente!\n\n")
        else:
            invalido = False
    return domain


def menu():
    opcao = ''
    while opcao != '1' and opcao != '2':
        print('===. Script para migração de contas entre servidores zimbra .=== ')
        print('1- Exportação\n2- Importação')
        opcao = input('')
        if opcao != '1' and opcao != '2':
            print('Opção inválida!\n\n')
    system('clear')
    return opcao


def verify_domain(domain):
    print("[+] Verificando Domínio...\n")
    return getstatusoutput('su - zimbra -c \'zmprov gd ' + domain + '\'')[0]


def verify_compresses_file(file_path):
    return path.isfile(file_path)


if __name__ == '__main__':
    migrations_dir = '/tmp/migracoes'
    zimbra_language = 'export LC_ALL=pt_BR.UTF-8;'
    main()

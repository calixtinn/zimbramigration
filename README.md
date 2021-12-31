# zimbraMigration

Script for migrating accounts between zimbra servers


## Preparation

- In the configuration of the domain to be exported/imported, there must be the correct configuration in: `Configure -> Domains -> General Information` for example:
    - "Service Computer's public name": `mail.<domain>` 
    - "Public Service Protocol": `https` or `http`
    - "Public service port": `7071`
    - An "A" entry must be created in the DNS zone for the domain: `mail.<domain>` pointing to the mail server IP.


- Run this script with `python3 migrate.py` on the Source mail server, and choose the option "1" to export

- The script will backup Mailboxes, Aliases, Distribution Lists, Filters of accounts of a domain.

- Copy the .tar.gz file generated on /tmp/ to target server

- Run the script with `python3 migrate.py` and choose the option "2".

- After run, the domain and this accounts will be restored!
    

    
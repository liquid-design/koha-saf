Ansible install-rol dat dit een ontbrekende seed is die nog in een latere iteratie moet toevoegen.

ssh ansible@bib-test.marxisme.be 'sudo koha-mysql bib-test -e "INSERT INTO biblio_framework (frameworkcode, frameworktext) VALUES (\"\", \"Default\");"'

Verifieer:
ssh ansible@bib-test.marxisme.be 'sudo koha-mysql bib-test -e "SELECT * FROM biblio_framework;"'
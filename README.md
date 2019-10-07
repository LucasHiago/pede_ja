# Noruh backend

Neste documento(e no código) você encontrará diversos códigos que a primeira vista podem não fazer sentido, quando isso acontecer você poderá encontrar tal referência [neste](https://docs.google.com/document/d/1SKX4I2pv7ONcCx9GfeGwvKGMI1Ya5tIO2gINREaEJUs/edit#heading=h.zf0o628gqfce) documento.

## Dependências

### Arch linux

sudo pacman -Sy gdal proj

### Ubuntu

sudo apt-get install build-essential libgdal20 libgdal-dev libgeos-3.6.2 libgeos-c1v5 libgeos-dev libproj-dev binutils libproj-dev gdal-bin gdal-data python-gdal

sudo apt-get install postgis

To install GDAL Use:

pip3 install --global-option=build_ext --global-option="-I/usr/include/gdal" GDAL=='gdal-config --version'

## Banco de dados

Este projeto necessita de geo referenciamento, por conta disso precisamos de um banco de dados que consiga lhe dar com estes tipos especiais de dados, para tal utilizamos o postgis. Como o processo de configuração pode ser demorado(e chato) dentro do diretório docker você pode executar o comando abaixo e ter a sua disposição o banco de dados pronto(lembre-se de executar as migrações):

```bash
cd docker && docker-compose up -d
```

## Variáveis de ambiente

Este projeto segue o [12factorApp](https://12factor.net/), como podemos ver no [factor 3](https://12factor.net/config) devemos ser capazes de modificar o comportamento de nossa aplicação simplesmente declarando variáveis de ambiente, para fazer isso crie um arquivo **.env** na raíz do projeto com uma das variáveis abaixo e seu respectivo valor.

- [DEBUG](https://docs.djangoproject.com/en/2.1/ref/settings/#debug)
- [DATABASE_URL](https://github.com/kennethreitz/dj-database-url#url-schema)
- [SECRET_KEY](https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-SECRET_KEY) - **ALWAYS change this value during production deployment**
- [ALLOWED_HOSTS](https://docs.djangoproject.com/en/2.1/ref/settings/#allowed-hosts)
- [LANGUAGE_CODE](https://docs.djangoproject.com/en/2.1/ref/settings/#language-code)

O projeto necessita de algumas variáveis de ambiente para executar determinados pontos do projeto.
Variaveis de ambiente para funcionar as features de enviar email, principalmente para recuperar senha, as variáveisde email são as seguintes:

- [EMAIL_HOST]
- [EMAIL_PORT]
- [EMAIL_USE_SSL]
- [EMAIL_FROM]
- [EMAIL_HOST_USER]
- [EMAIL_HOST_PASSWORD]
- [EMAIL_BACKEND]

Também são necesárias as variáveis de ambiente para o Pusher Notifications(notificações no web), que são as seguintes abaixo:
- [PUSHER_APP_ID]
- [PUSHER_KEY]
- [PUSHER_SECRET]
- [PUSHER_CLUSTER]
- [PUSHER_SSL]

Para as notificações push serem enviadas para os devices, utilizamos a lib **fcm-django**(https://fcm-django.readthedocs.io/en/latest/). Essa lib, necessita dessas variáveis de ambiente a seguir para funcionar corretamente.

- [FCM_SERVER_KEY]
- [ONE_DEVICE_PER_USER]

Outra variável de ambiente que deve ser configurada, são duas variáveis de ambiente da lib **celery** (http://docs.celeryproject.org/en/latest/django/). O celery, é uma lib para rodar tasks em background, atualmente no projeto, o celery é utilizado para verificações de quando um pagamento foi aprovado ou não. As variáveis de ambiente do Celery são:

- [CELERY_BROKER_URL]
- [CELERY_RESULT_BACKEND]

O formato do arquivo .env é muito simples, siga o exemplo abaixo:

```bash
VARIABLE=VALUE
```

## Perfil dos usuários

Os perfis são gerenciados através de grupos, por padrão existem os seguintes perfis(grupos):

* Administrador estabelecimento
* Cozinha
* Garçom
* Funcionário estabelecimento
* Consumidor

    Não existe grupo super admin, para isso é preciso setar a flag Superuser para cada usuário que necessitar desse nível de acesso. **Atenção** tenha muito cuidado ao conceder esse nível de acesso pois ele não **possui restrições**.

### Criar Permissões e grupos padrões para configurar ambiente

As permissões também podem ser trabalhadas de uma forma diferente, o projeto possui as permissões para acesso ao Web View criadas no modelo de cada objeto, utilizando campo permissions do Modelo na class Meta. Com essa permissão criada, ela pode ser atribuída a cada tipo de view específica. Por exemplo, no modelo Establishment, existe a permissão para pode ver o Objeto do tipo Establishment, daí a permissão para ver o objeto do tipo Establishment, é atribuída na view.(Ex: "'app':can_view_establishment").

Para que essa configuração funcione, é **necessário configurar o banco e executar as migrações no banco com o comando python manage.py migrate**

Para criar todos os grupos, e associar cada permissão específica a cada grupo, nós rodamos o comando:

```bash
python manage.py dumpdata create_groups_and_permissions
```
Esse comando, contém as informações dos tipos de grupos criados, e de todas as permissões. Com esse arquivo, é possível carregar em outro ambiente, para já ter as permissões configuradas.

Se durante o desenvolvimento for necessário criar novas permissões, ou remover, ou alterar permissões, o arquivo para realizar manutenção nessas permissões é bastante simples. Ele está localizado em **/register/management/commands/create_groups_and_permissions.py**. O arquivo contem um método chamado **create_groups_and_permissions**, que recebe como parametro um objeto do tipo Grupo, e uma lista de permissões. Nessa lista de permissões, é realizado uma iteração, e a partir realiza uma busca da permissão no banco, e adiciona ela ao respectivo grupo que foi passado como parametro ao chamar o metodo.

Para o chamar o método, é bastante simples, basta criar um grupo e uma lista de strings com o **codename** de cada permissão, e com isso chama o método.

### Como atualizar os profiles iniciais

Também durante o desenvolvimento, podem ser criados grupos, tipos de permissões, atribuição de permissões para determinados grupos, ou trocas dessas permissões entre os grupos utilizando o django-admin, após isso, pode atualizar o arquivo **groups.yaml**, utilizando o comando

```bash
python manage.py dumpdata --format yaml auth.Group > register/fixtures/initial_data.yaml
```

## Membros adicionais de uma conta

Assim que uma conta é criada ela possui um proprietário, porém outros membros podem fazer parte da mesma conta.

Para adicionar membros a uma conta siga o exemplo abaixo:

```python
BillMember(bill=my_bill, customer=a_new_member).save()
```

O campo joined_at é preenchido automaticamente.
O campo leave_at é preenchido pelo método de instância leave_bill

**Nunca** manipule diretamente os campos joined_at e leave_at!

## Proprietário de uma conta

Sempre que abrir uma nova conta(Bill) você deve associá-lo como membro dessa conta(BillMember), o membro mais antigo será sempre o dono.

> O RF015 descreve que o dono da conta pode escolher sair e deixar o débito com os outros participantes. Neste caso basta chamar o método de instância __leave()__.

> Se o último membro da conta tentar deixá-la(__leave()__) a exceção **CannotLeaveBillException** será levantada.

## Estatísticas

Foi criada a classe EstablishmentStatistics para armazenar todo tipo de estatística que se fizer necessário. Essa classe não deve ser manipulada diretamente, um background scheduled job deve ser criado para ficar populando essa tabela.

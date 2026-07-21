# django_base — Documentação de Arquitetura

Projeto base Django reutilizável, com sistema de autenticação, controle de usuários, departamentos e autorização granular. Construído para servir como ponto de partida para futuros projetos.

---

## 1. Visão geral das decisões estruturais

| Decisão | Escolha | Motivo |
|---|---|---|
| Nome do projeto | `django_base` | Explícito, sem metáfora — fácil de entender ao retomar o projeto depois de meses |
| Admin nativo (`django.contrib.admin`) | Não utilizado | Painel administrativo próprio será construído (inicialmente sem frontend definido) |
| Sistema de permissão nativo (`Group`/`Permission` do Django) | Não utilizado | `Group` cria vínculo *vivo* (permissão via grupo); requisito é permissão vinculada diretamente ao usuário, com sincronização manual |
| `PermissionsMixin` | Não utilizado | Controle total sobre autorização, sem duas fontes de verdade (nativa + customizada) coexistindo |
| Identificador de login | `email` (não `username`) | Decisão de produto — sem campo `username` |
| Superusuário | Campo `is_superuser` próprio, verificado manualmente na função central de checagem | Mecanismo de "break glass" (conta mestra), independente do sistema de permissões customizado |

---

## 2. Estrutura de apps

```
django_base/
├── accounts/         # User customizado (autenticação, dados do próprio usuário)
├── departments/       # Department + vínculo User↔Department
└── authorization/      # Permission + vínculo User↔Permission + templates de departamento
```

### Regra de dependência entre apps

```
accounts  ←  departments  ←  authorization
```

Dependência em uma única direção, sem ciclos:
- `accounts` não depende de nenhum outro app do domínio.
- `departments` depende de `accounts` (campos de auditoria `created_by`/`updated_by`).
- `authorization` depende de `accounts` e `departments` (permissões referenciam usuário e, opcionalmente, departamento de origem).

**Por quê importa:** uma dependência circular entre apps é sinal de fronteira mal desenhada, mesmo quando o Django permite resolver tecnicamente via referência por string.

### Critério usado para decidir em qual app uma tabela de vínculo mora

A tabela de vínculo pertence ao app que representa o conceito **mais específico** da relação, não o mais genérico. Por isso:
- `UserDepartment` mora em `departments` (não em `accounts`) — é uma regra específica de departamento, não de usuário em si.
- `UserPermission` e `DepartmentPermissionTemplate` moram juntos em `authorization` — ambos são regras de autorização, mesmo um deles envolvendo `Department`.

Isso mantém `accounts` genérico e reutilizável isoladamente em outros projetos, sem carregar lógica de departamento/autorização junto.

---

## 3. Modelo de dados (DBML)

```dbml
Table users {
  id integer [pk]
  email varchar [unique]
  password varchar
  first_name varchar
  last_name varchar
  phone varchar
  is_active boolean [default: true]
  is_superuser boolean
  created_at timestamp
  updated_at timestamp
  deleted_at timestamp [null]
}

Table departments {
  id integer [pk]
  name varchar
  description text
  is_active boolean [default: true]
  created_by_id integer [ref: > users.id, null]
  updated_by_id integer [ref: > users.id, null]
  created_at timestamp
  updated_at timestamp
}

Table user_departments {
  id integer [pk]
  user_id integer [ref: > users.id]
  department_id integer [ref: > departments.id]
  granted_by_id integer [ref: > users.id, null]
  created_at timestamp // 
 
  indexes {
    (user_id, department_id) [unique]
  }
}

Table permissions {
  id integer [pk]
  code varchar [unique]
  name varchar
  description text
  is_active boolean [default: true]
  created_at timestamp
  updated_at timestamp
}

Table user_permissions {
  id integer [pk]
  user_id integer [ref: > users.id]
  permission_id integer [ref: > permissions.id]
  source varchar [note: 'enum: manual, department']
  origin_department_id integer [ref: > departments.id, null]
  granted_by_id integer [ref: > users.id, null]
  created_at timestamp

  indexes {
    (user_id, permission_id) [unique]
  }
}

Table department_permission_templates {
  id integer [pk]
  department_id integer [ref: > departments.id]
  permission_id integer [ref: > permissions.id]
  created_at timestamp

  indexes {
    (department_id, permission_id) [unique]
  }
}
```

---

## 4. Decisões conceituais importantes

### 4.1 Autorização vinculada ao usuário, não ao departamento

O departamento tem um **modelo/template** de permissões (`DepartmentPermissionTemplate`), mas a permissão real do usuário sempre vive em `UserPermission` — nunca é consultada "através" do departamento em tempo real.

**Sincronização é manual e pontual**, não automática/reativa:
- Alterar o template de um departamento **não** propaga automaticamente para usuários já vinculados.
- Existe uma ação explícita ("aplicar modelo do departamento a este usuário") que copia as permissões do template para `UserPermission`, marcando `source = department` e `origin_department_id`.
- Isso permite auditar quais permissões vieram de onde, e decidir manualmente quando ressincronizar.

### 4.2 `source` como origem, não como vínculo vivo

`UserPermission.source` (`manual` ou `department`) e `origin_department_id` são **metadados históricos**. Editar os departamentos de um usuário (`UserDepartment`) é uma ação independente e não afeta permissões já concedidas — mesmo que o usuário saia do departamento de origem, a permissão e seu histórico permanecem intactos.

### 4.3 `is_active` vs `deleted_at` em `users` — eixos independentes

Decisão explícita de produto: os dois campos **não se implicam**.
- `is_active = False` → usuário inativo, mas o registro continua existindo normalmente.
- `deleted_at != null` → usuário soft-deletado, mas pode estar com `is_active = True` ou `False`.

**Implicação prática:** qualquer checagem de autenticação/autorização precisa validar os dois campos separadamente — nunca assumir que um implica o outro.

### 4.4 `is_active` em `departments` e `permissions` — desativação, não exclusão

Departamentos e permissões usam `is_active` (não soft delete/`deleted_at`) porque a necessidade real é impedir *novo uso* (não aparecer como opção ao vincular), preservando todo o histórico já existente em `UserPermission`/`DepartmentPermissionTemplate` intacto.

### 4.5 Soft delete apenas em `users`

- `deleted_at` existe **somente** na tabela `users`.
- `departments` e `permissions` não têm soft delete — são tratados como catálogo, controlados via `is_active`.
- E-mail de usuário deletado é reutilizável (por isso `unique=True` e quando é deletado o e-mail é alterado com um prefixo que marca).

### 4.6 Função central de checagem de permissão

Toda verificação de autorização no sistema deve passar por **um único ponto** (planejado para `authorization/services.py`), nunca ser reimplementada em views individuais. Essa função é responsável por:
1. Verificar se o usuário está deletado ou inativo (bloqueia de imediato).
2. Verificar `is_superuser` (retorna `True` sempre, sem checar mais nada).
3. Verificar se a permissão em si está `is_active`.
4. Consultar `UserPermission` para o vínculo real.

Centralizar isso evita que alguém esqueça de checar `is_superuser` ou `is_active` numa view nova, criando inconsistência.

---

## 5. Campos de auditoria — padrão adotado

| Campo | Presente em | Observação |
|---|---|---|
| `created_at` | Todas as tabelas | Timestamp de criação |
| `updated_at` | Tabelas de "estado editável" (`users`, `departments`, `permissions`) | Ausente nas tabelas de vínculo/evento, que representam um registro pontual, não algo editável |
| `deleted_at` | Somente `users` | Soft delete |
| `created_by_id` / `updated_by_id` | `departments` | Rastro de quem criou/editou |
| `granted_by_id` | `user_departments`, `user_permissions` | Rastro de quem concedeu o vínculo (nullable — permite seed inicial sem usuário concedente) |

Todas as FKs para o model de usuário usam `on_delete=models.SET_NULL` (nunca `CASCADE`), preservando o registro principal mesmo que o usuário responsável seja removido.

---

## 6. Padrões técnicos do Django adotados

- **`AUTH_USER_MODEL = "accounts.User"`** — configurado antes da primeira migration (decisão irreversível sem reset de banco).
- **`AbstractBaseUser` sem `PermissionsMixin`** — controle total sobre campos e sem duplicidade de mecanismo de autorização.
- **`Manager` customizado (`UserManager`)** — filtra `deleted_at__isnull=True` por padrão em toda consulta, evitando vazamento de usuários deletados em listagens.
- **`ForeignKey` para usuário via `settings.AUTH_USER_MODEL`**, nunca importando `User` diretamente — evita import circular e segue a prática recomendada do Django.
- **Referência de model entre apps via string** (ex: `"departments.Department"`) — necessário pela direção de dependência `accounts ← departments ← authorization`.
- **`TextChoices`** para campos de opções fixas (ex: `UserPermission.Source`) — centraliza valores válidos, evita inconsistência de string livre.
- **`Meta.constraints` com `UniqueConstraint`** (não `unique_together`, que está sendo depreciado) para unicidade composta.
- **Telefone como `CharField` (não numérico)** — armazena apenas dígitos, mas é identificador textual, não valor aritmético; validação de formato via `RegexValidator`, não via tipo de coluna.

---

## 7. Reaproveitamento futuro — API

A separação em Models + `services.py` (regra de negócio) foi pensada para ser **independente da camada de exposição** (views tradicionais vs API). Quando este projeto (ou uma cópia dele) precisar virar API:

- Models, managers, constraints e `services.py` são reaproveitados sem alteração.
- Adiciona-se `serializers.py` por app e `rest_framework` ao `INSTALLED_APPS`.
- Autenticação ganha uma camada JWT (`djangorestframework-simplejwt`) por cima da autenticação já existente.

Recomendação: manter `django_base` (este projeto, sem DRF) e criar um template irmão `django_api_base` a partir de uma cópia, em vez de misturar os dois propósitos num só template.

---
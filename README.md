Dataiku DSS collection
===================

This collection packages custom modules to administrate Dataiku Data Science Studio platforms.


Installation
------------

### Basic

If the first directory of your roles path is writable, just use:

 ```
ansible-galaxy collection install git+https://github.com/dataiku/dataiku-ansible-collection
 ```

Or specify the path in which you want the role to be installed:

 ```
ansible-galaxy collection install git+https://github.com/dataiku/dataiku-ansible-collection
 ```

### Force update

If the collection already exists, `ansible-galaxy` will not update it unless the `--force` flag is set.

### Automation and versioning

You can use a `yaml` file with a content like this:

```YAML
---
- src: git+https://github.com/dataiku/dataiku-ansible-collection
  name: dataiku-ansible-collection
  version: master
```

Then install it like this:

```bash
ansible-galaxy install -r /path/to/your/file.yml
```

This allows you to:
- Force a specific version
- Rename the role on the fly



Basic Usage
----------------

## Using Modules

```YAML
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dataiku.dss.dss_get_credentials:
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info

    - dataiku.dss.dss_group:
        connect_to: "{{ dss_connection_info }}"
        name: datascienceguys

    - dataiku.dss.dss_user:
        connect_to: "{{ dss_connection_info }}"
        login: myadmin
        password: theadminpasswordveryverystrongindeed
        groups: [administrators,datascienceguys]

    - dataiku.dss.dss_general_settings:
        connect_to: "{{ dss_connection_info }}"
        settings:
          ldapSettings:
            enabled: true
            url: ldap://ldap.internal.example.com/dc=example,dc=com
            bindDN: uid=readonly,ou=users,dc=example,dc=com
            bindPassword: theserviceaccountpassword
            useTls: true
            autoImportUsers: true
            userFilter: (&(objectClass=posixAccount)(uid={USERNAME}))
            defaultUserProfile: READER
            displayNameAttribute: gecos
            emailAttribute: mail
            enableGroups: true
            groupFilter: (&(objectClass=posixGroup)(memberUid={USERDN}))
            groupNameAttribute: cn
            groupProfiles: []
            authorizedGroups: 
              - dss-users
```

## Using Roles

Using Roles from a playbook
```YAML
- hosts: servers
  become: true
  roles:
    - name: dataiku.dss.install_telegraf
      vars:
        telegraf_conf_dss_datadir: /data/dataiku/dss_data
        telegraf_conf_dss_id: test-collections
        telegraph_hostname: dss.example.com
    
    - name: dataiku.dss.install_tesseract
      vars:
        force_install: "{{ dataiku_dss_was_installed or dataiku_dss_was_upgraded }}"
```

Using Roles from a task
```YAML
tasks:
  - import_role:
      name: dataiku.dss.install_telegraf
    vars:
      telegraf_conf_dss_datadir: /data/dataiku/dss_data
      telegraf_conf_dss_id: test-collections
      telegraph_hostname: dss.example.com

  - import_role:
      name: dataiku.dss.install_tesseract
    vars:
      force_install: "{{ dataiku_dss_was_installed or dataiku_dss_was_upgraded }}"
```


Migrating from dataiku-ansible-modules
-----------------------------------------

The modules published in this collection are the same as the modules published in dataiku-ansible-modules. Their usage is the same, the only required changes are the way ansible access modules of collections.
In a collection, modules are referenced as `collection_namespace.collection_name.module_name`

Therefore, the module usage
```YAML
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dss_get_credentials:          # becomes dataiku.dss.dss_get_credentials
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info
```

simply becomes :
```YAML
- hosts: servers
  become: true
  become_user: dataiku
  tasks:
    - dataiku.dss.dss_get_credentials:
        datadir: /home/dataiku/dss
        api_key_name: myadminkey
      register: dss_connection_info
```

Alternatively, the environment variable `ANSIBLE_COLLECTION_PATH` can be leveraged so that ansible auto discovers the right modules

# Selectel DNS provider for octoDNS

An [octoDNS](https://github.com/octodns/octodns/) provider that targets [Selectel DNS](https://docs.selectel.com/cloud-services/dns-hosting/dns_hosting/).

### Installation

#### Command line

```bash
pip install octodns-selectel
```

#### requirements.txt/setup.py

Pinning specific versions is recommended to avoid unplanned upgrades.

##### Versions

```
# Start with the latest versions and don't just copy what's here
octodns==1.4.0
octodns-selectel==1.0.0
```

### Configuration

#### Selectel Provider

```yaml
providers:
  selectel:
    class: octodns_selectel.SelectelProvider
    token: env/KEYSTONE_PROJECT_TOKEN
```

For receive KEYSTONE_PROJECT_TOKEN read [here](#token-for-provider)

### Examples

Structure folders

```bash
├── config.yaml
└── zones
    ├── octodns-test-alias.com.yaml
    └── octodns-test.com.yaml
```

```yaml
# ./config.yaml
providers:
  config:
    class: octodns.provider.yaml.YamlProvider
    directory: ./zones
    default_ttl: 3600
    enforce_order: True
  selectel:
    class: octodns_selectel.SelectelProvider
    token: env/KEYSTONE_PROJECT_TOKEN
zones:
  octodns-test.com.:
    sources:
      - config
    targets:
      - selectel
  octodns-test-alias.com.:
    sources:
      - config
    targets:
      - selectel
```

```yaml
# ./zones/octodns-test.com.yaml
'':
  - ttl: 3600
    type: A
    values:
      - 1.2.3.4
      - 1.2.3.5
  - ttl: 3600
    type: AAAA
    values: 
      - 6dc1:b9af:74ca:84e9:6c7c:5c0f:c292:9188
      - 5051:e345:9038:052c:00db:eb98:d871:8ae6
  - ttl: 3600
    type: MX
    value:
      exchange: mail1.octodns-test.com.
      preference: 10
  - ttl: 3600
    type: TXT
    values: 
      - "bar"
      - "foo"

_sip._tcp:
  - ttl: 3600
    type: SRV
    values:
    - port: 5060
      priority: 10
      target: phone1.example.com.
      weight: 60
    - port: 5030
      priority: 20
      target: phone2.example.com.
      weight: 0     

foo:
  - ttl: 3600
    type: CNAME
    value: bar.octodns-test.com.

oldns:
  - ttl: 3600
    type: NS
    values:
      - ns1.selectel.com.
      - ns2.selectel.com.

sshfp:
  - ttl: 3600
    type: SSHFP
    values:
    - algorithm: 1
      fingerprint: "4158f281921260b0205508121c6f5cee879e15f22bdbc319ef2ae9fd308db3be"
      fingerprint_type: 2
    - algorithm: 4
      fingerprint: "123456789abcdef67890123456789abcdef67890123456789abcdef123456789"
      fingerprint_type: 2

txt:
  - ttl: 3600
    type: TXT
    values: 
      - "bar_txt"
      - "foo_txt"
```

```yaml
# ./zones/octodns-test-alias.com.yaml
'':
  - ttl: 3600
    type: ALIAS
    value: octodns-test.com.
```

Use command:

```bash
$octodns-sync --config-file=config.yaml
```

#### Migrating from DNS V1 to DNS V2

```yaml
# ./config-migrate.yaml
processors:
  # Selectel doesn't allow manage Root NS records
  # for skipping root ns use IgnoreRootNsFilter class
  no-root-ns:
    class: octodns.processor.filter.IgnoreRootNsFilter
providers:
  selectel_v1:
    class: octodns_selectel.SelectelProviderLegacy
    token: env/SELECTEL_TOKEN
  selectel_v2:
    class: octodns_selectel.SelectelProvider
    token: env/KEYSTONE_PROJECT_TOKEN
zones: 
  "*":
    sources:
    - selectel_v1
    processors:
    - no-root-ns
    targets:
    - selectel_v2
```

Use command:

```bash
$octodns-sync --config-file=config-migrate.yaml
```

#### Token for ProviderLegacy

Use Selectel Token.
More information about Selectel Token read [here](https://developers.selectel.com/docs/control-panel/authorization/#selectel-token-api-key).

#### Token for Provider

Use Keystone Project Token.
More information about Keystone Project Token read [here](https://developers.selectel.com/docs/control-panel/authorization/#project-token).

### Support Information

#### Records

SelectelProvider supports A, AAAA, ALIAS, CNAME, MX, NS, SRV, SSHFP and TXT

#### Dynamic

SelectelProvider does not support dynamic records.

### Development

See the [/script/](/script/) directory for some tools to help with the development process. They generally follow the [Script to rule them all](https://github.com/github/scripts-to-rule-them-all) pattern. Most useful is `./script/bootstrap` which will create a venv and install both the runtime and development related requirements. It will also hook up a pre-commit hook that covers most of what's run by CI.

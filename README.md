## Selectel DNS provider for octoDNS

An [octoDNS](https://github.com/octodns/octodns/) provider that targets [Selectel DNS](https://selectel.ru/en/services/additional/dns/).

### Installation

#### Command line

```
pip install octodns-selectel
```

#### requirements.txt/setup.py

Pinning specific versions or SHAs is recommended to avoid unplanned upgrades.

##### Versions

```
# Start with the latest versions and don't just copy what's here
octodns==0.9.17
octodns-selectel==0.0.3
```

##### SHAs

```
# Start with the latest/specific versions and don't just copy what's here
-e git+https://git@github.com/octodns/octodns.git@9da19749e28f68407a1c246dfdf65663cdc1c422#egg=octodns
-e git+https://git@github.com/octodns/octodns-selectel.git@ec9661f8b335241ae4746eea467a8509205e6a30#egg=octodns_selectel
```

### Configuration

| :memo:        | Use SelectelProviderV2  |
|---------------|:------------------------|

#### Selectel Provider V1

```yaml
providers:
  selectel:
    class: octodns_selectel.SelectelProviderV1
    token: env/SELECTEL_TOKEN
```

#### Selectel Provider V2

```yaml
providers:
  selectel:
    class: octodns_selectel.SelectelProviderV2
    token: env/KEYSTONE_PROJECT_TOKEN
```

#### Token for Provider V1

Use Selectel Token.
More information about Selectel Token read [here](https://developers.selectel.com/docs/control-panel/authorization/#selectel-token-api-key).

#### Token for Provider V2

Use Keystone Project Token.
More information about Keystone Project Token read [here](https://developers.selectel.com/docs/control-panel/authorization/#project-token).

### Migrating from DNS V1 to DNS V2

```yaml
---
processors:
  no-root-ns:
    class: octodns.processor.filter.IgnoreRootNsFilter
providers:
  selectel_v1:
    class: octodns_selectel.SelectelProviderV1
    token: env/SELECTEL_TOKEN
  selectel_v2:
    class: octodns_selectel.SelectelProviderV2
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

### Support Information

#### Records

SelectelProviderV1 and SelectelProviderV2 supports:

1. A;
2. AAAA;
3. ALIAS;
4. CNAME;
5. MX;
6. NS;
7. SRV;
8. SSHFP
9. TXT

#### Dynamic

SelectelProviderV1 and SelectelProviderV2 does not support dynamic records.

### Development

See the [/script/](/script/) directory for some tools to help with the development process. They generally follow the [Script to rule them all](https://github.com/github/scripts-to-rule-them-all) pattern. Most useful is `./script/bootstrap` which will create a venv and install both the runtime and development related requirements. It will also hook up a pre-commit hook that covers most of what's run by CI.

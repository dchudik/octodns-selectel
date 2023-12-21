from string import Template

from .exceptions import SelectelException


def to_selectel_rrset(record):
    rrset = dict(name=record.fqdn, ttl=record.ttl, type=record._type)
    rrset_records = []
    content_mx_tmpl = Template("$preference $exchange")
    content_srv_tmpl = Template("$priority $weight $port $target")
    content_sshfp_tmpl = Template("$algorithm $fingerprint_type $fingerprint")
    match record._type:
        case "A" | "AAAA" | "NS" | "TXT":
            rrset_records = list(
                map(lambda value: {'content': value}, record.values)
            )
        case "CNAME" | "ALIAS":
            rrset_records = [{'content': record.value}]
        # TODO: fix error: parsed as \'"foo2"\' got 422
        # {'error': 'bad_request', 'description': 'Not in expected format (parsed as \'"foo2"\')'}
        # case "TXT":
        #     rrset_records = list(
        #         map(lambda value: {'content': f'{value}'}, record.values)
        #     )
        case "MX":
            rrset_records = list(
                map(
                    lambda value: {
                        'content': content_mx_tmpl.substitute(
                            preference=value.preference, exchange=value.exchange
                        )
                    },
                    record.values,
                )
            )
        case "SRV":
            rrset_records = list(
                map(
                    lambda value: {
                        'content': content_srv_tmpl.substitute(
                            priority=value.priority,
                            weight=value.weight,
                            port=value.port,
                            target=value.target,
                        )
                    },
                    record.values,
                )
            )
        case "SSHFP":
            rrset_records = list(
                map(
                    lambda value: {
                        'content': content_sshfp_tmpl.substitute(
                            algorithm=value.algorithm,
                            fingerprint_type=value.fingerprint_type,
                            fingerprint=value.fingerprint,
                        )
                    },
                    record.values,
                )
            )
        case _:
            raise SelectelException(
                f'DNS Record with type: {record._type} not supported'
            )
    rrset["records"] = rrset_records
    return rrset


def to_octodns_record(rrset):
    rrset_type = rrset["type"]
    octodns_record = dict(type=rrset_type, ttl=rrset["ttl"])
    record_values = []
    match rrset_type:
        case "A" | "AAAA" | "NS" | "TXT":
            record_values = [r['content'] for r in rrset["records"]]
        case "CNAME" | "ALIAS":
            record_values = rrset["records"][0]["content"]
        # TODO: fix unwrap TXT
        # case "TXT":
        #     print([r['content'] for r in rrset["records"]])
        #     print([r['content'].strip('\"') for r in rrset["records"]])
        #     record_values = [r['content'].strip('\"') for r in rrset["records"]]
        case "MX":
            for record in rrset["records"]:
                preference, exchange = record["content"].split(" ")
                record_values.append(
                    {'preference': preference, 'exchange': exchange}
                )
        case "SRV":
            for record in rrset["records"]:
                priority, weight, port, target = record["content"].split(" ")
                record_values.append(
                    {
                        'priority': priority,
                        'weight': weight,
                        'port': port,
                        'target': target,
                    }
                )
        case "SSHFP":
            for record in rrset["records"]:
                algorithm, fingerprint_type, fingerprint = record[
                    "content"
                ].split(" ")
                record_values.append(
                    {
                        'algorithm': algorithm,
                        'fingerprint_type': fingerprint_type,
                        'fingerprint': fingerprint,
                    }
                )
        case _:
            raise SelectelException(
                f'DNS Record with type: {rrset_type} not supported'
            )
    octodns_record["values"] = record_values
    return octodns_record

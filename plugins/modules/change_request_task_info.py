#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r"""
module: change_request_task_info

author:
  - Matej Pevec (@mysteriouswolf)
  - Manca Bizjak (@mancabizjak)
  - Miha Dolinar (@mdolin)
  - Tadej Borovsak (@tadeboro)
  
short_description: List ServiceNow change request tasks
description:
  - Retrieve information about ServiceNow change request tasks.
  - For more information, refer to the ServiceNow change management documentation at
    U(https://docs.servicenow.com/bundle/paris-it-service-management/page/product/change-management/concept/c_ITILChangeManagement.html).
version_added: 1.0.0
extends_documentation_fragment:
  - servicenow.itsm.instance
  - servicenow.itsm.sys_id.info
  - servicenow.itsm.number.info
  - servicenow.itsm.query
seealso:
  - module: servicenow.itsm.change_request_task
"""

EXAMPLES = r"""
- name: Retrieve all change request tasks
  servicenow.itsm.change_request_task_info:
  register: result

- name: Retrieve a specific change request task by its sys_id
  servicenow.itsm.change_request_task_info:
    sys_id: 471bfbc7a9fe198101e77a3e10e5d47f
  register: result

- name: Retrieve change request tasks by number
  servicenow.itsm.change_request_task_info:
    number: CTASK0000001
  register: result

- name: Retrieve change request tasks that contain SAP in their short description
  servicenow.itsm.change_request_task_info:
    query:
      - short_description: LIKE SAP
  register: result

- name: Retrieve new change requests assigned to abel.tuter or bertie.luby
  servicenow.itsm.change_request_task_info:
    query:
      - state: = new
        assigned_to: = abel.tuter
      - state: = new
        assigned_to: = bertie.luby
"""

RETURN = r"""
records:
  description:
    - A list of change task records.
  returned: success
  type: list
  sample:
    - TBD
"""

from ansible.module_utils.basic import AnsibleModule

from ..module_utils import arguments, client, errors, query, utils, table
from ..module_utils.change_request_task import PAYLOAD_FIELDS_MAPPING


def remap_params(query, table_client):
    query_load = []

    for item in query:
        q = dict()
        for k, v in item.items():
            if k == "type":
                q["change_task_type"] = (v[0], v[1])

            elif k == "hold_reason":
                q["on_hold_reason"] = (v[0], v[1])

            elif k == "configuration_item":
                q["cmdb_ci"] = (v[0], v[1])

            elif k == "change_request_id":
                q["change_request"] = (v[0], v[1])

            elif k == "change_request_number":
                change_request = table.find_change_request(table_client, v[1])
                q["change_request"] = (v[0], change_request["sys_id"])

            elif k == "assigned_to":
                user = table.find_user(table_client, v[1])
                q["assigned_to"] = (v[0], user["sys_id"])

            elif k == "assignment_group":
                assignment_group = table.find_assignment_group(table_client, v[1])
                q["assignment_group"] = (v[0], assignment_group["sys_id"])

            else:
                q[k] = v

        query_load.append(q)

    return query_load


def sysparms_query(module, table_client, mapper):
    parsed, err = query.parse_query(module.params["query"])
    if err:
        raise errors.ServiceNowError(err)

    remap_query = remap_params(parsed, table_client)

    return query.serialize_query(query.map_query_values(remap_query, mapper))


def run(module, table_client):
    mapper = utils.PayloadMapper(PAYLOAD_FIELDS_MAPPING, module.warn)

    if module.params["query"]:
        query = {"sysparm_query": sysparms_query(module, table_client, mapper)}
    else:
        query = utils.filter_dict(module.params, "sys_id", "number")

    return [
        mapper.to_ansible(record)
        for record in table_client.list_records("change_task", query)
    ]


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            arguments.get_spec("instance", "sys_id", "number", "query"),
        ),
        mutually_exclusive=[("sys_id", "query"), ("number", "query")],
    )

    try:
        snow_client = client.Client(**module.params["instance"])
        table_client = table.TableClient(snow_client)
        records = run(module, table_client)
        module.exit_json(changed=False, records=records)
    except errors.ServiceNowError as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()

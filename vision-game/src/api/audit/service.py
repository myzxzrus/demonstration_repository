import json
import os
import subprocess
from io import BufferedReader, BytesIO
from typing import List

from odtemplater import ConfigurationMyOdt, ODTemplater
from sqlalchemy.orm import Session
from ...models import Audit
from ...tools.request_service import BaseModelRequest


class BaseModelRequestAudit(BaseModelRequest):
    def __init__(self, session: Session, **kwargs):
        super().__init__(session, Audit, **kwargs)


class ReportAuditService:

    data = {'document_name': 'report_audit',
            'document_template_binary': b'PK\x03\x04\x14\x00\x00\x08\x00\x00...',
            'content': {
                'text_and_table_content': [],
                'extend_set': [],
            }
            }
    base_path = f'{os.path.dirname(os.path.abspath(__file__))}/../../templates'

    def __init__(self, session: Session, **kwargs):
        self.session = session
        self.filters = self._get_filters(kwargs['filters']) if 'filters' in kwargs else None
        self.result = BaseModelRequestAudit(session, filters=kwargs['filters'] if 'filters' in kwargs else None).make_response()
        self.file_template = self.base_path + '/audit_reports.odt'

    def _get_filters(self, filters):
        if type(filters) == str:
            filters_obj = json.loads(filters)
            return filters_obj

    def _make_date(self):
        start_date = {'key_': 'start_date', 'render_text': self.result['response'][-1].date.strftime('%d.%m.%Y %H:%M:%S')}
        end_date = {'key_': 'end_date', 'render_text': self.result['response'][0].date.strftime('%d.%m.%Y %H:%M:%S')}
        self.data['content']['text_and_table_content'].append(start_date)
        self.data['content']['text_and_table_content'].append(end_date)

    def _make_table(self):
        res: List[Audit] = self.result['response']
        table_row = []
        for ind, val in enumerate(res):
            temp_row = []
            val: Audit = val
            temp_row.append({'key_': f'n{ind + 1}', 'render_text': f'{ind+1}'})
            temp_row.append({'key_': f'user{ind + 1}', 'render_text': f'{val.user}'})
            temp_row.append({'key_': f'date{ind + 1}', 'render_text': f'{val.date}'})
            temp_row.append({'key_': f'action{ind + 1}', 'render_text': f'{val.action}'})
            table_row.append(temp_row)
        self.data['content']['extend_set'] = [
            {'key_': 'g', 'content': table_row}
        ]

    def _open_template(self):
        with open(self.file_template, 'rb') as text:
            self.data['document_template_binary'] = text.read()

    def make_report(self):
        self._make_date()
        self._make_table()
        self._open_template()
        setattr(ConfigurationMyOdt, 'path_template_folder', self.base_path + '/temp/')
        doc = ODTemplater(self.data)
        doc_out = doc.create()
        with open(self.base_path + '/temp/out/audit_response.odt', 'wb') as file_out:
            file_out.write(doc_out)
        subprocess.run(["libreoffice", "--headless", "--convert-to", "docx", self.base_path + '/temp/out/audit_response.odt', "--outdir", self.base_path + '/temp/out/'])
        return self.base_path + '/temp/out/audit_response.docx'


class AuditStatistic:
    def __init__(self):
        ...


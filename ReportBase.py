#-*- coding:utf-8 -*-
import argparse
from VarBase import VarBase
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import json
import os
import re

class ReportBase(VarBase):
    def __init__(self, json_name, output_div):
        super().__init__(json_name, output_div)

        self.data = {}
        # 个人信息
        self.data['sample'] = dict()
        # qc
        self.data['qc'] = dict()
        self.data["lib_quality_control"] = dict()
        # 变异汇总
        self.data['var'] = dict()
        # drug
        self.data['drug'] = dict()
        # 治疗方案
        self.data['therapeutic_regimen'] = dict()
        # 临床试验
        self.data['clinic_trial'] = dict()
        # PD-L1
        self.data['pdl1'] = dict()
        # MSI
        self.data['msi'] = dict()
        # TMB
        self.data['tmb'] = dict()
        # RNA表达
        self.data['rna_exp'] = dict()
        # 化疗结果
        self.data['chemo'] = dict()
        # 肺癌GEP
        self.data['gep'] = dict()
        # TME
        self.data['tme'] = dict()
        # HRD
        self.data['hrd'] = dict()
        
        # 参考文献
        self.data['refer'] = dict()
    
    def run(self):
        report_name = self.MatchReport()
        self.data['sample'] = self.sample_info()
        self.data['qc'], self.data['lib_quality_control'] = self.getQC()
        self.data['therapeutic_regimen'] = self.getRegimen()
        self.data['drug'] = self.getDrug()
        self.data['gep'] = self.getGEP()
        self.data['msi'] = self.getMSI()
        self.data['pdl1'] = self.getPDL1()
        self.data['tmb'] = self.getTMB()
        self.data['tme'] = self.getTME()
        self.data['clinic_trial'] = self.getClinic()
        self.data['rna_exp'] = self.getRNAExp()
        self.data['chemo'] = self.getchemo()
        self.data['var'] = self.getVar()
        self.data['refer']['fixed'] = self.getfixed_refer(report_name, self.data['sample']['tumor_list'])
        self.data['refer']['dynamic'] =  self.getdynamic_refer(self.data['var'], self.data['hrd'])
        # 输出构建好的用来填充模板的data
        self.dataJson = json.dumps(self.data, ensure_ascii=False)
        with open(self.output_div + '/' + self.json_name + '_to_word.json', 'w', encoding='utf-8') as outFile:
            outFile.write(self.dataJson)

        return self.data

    def renderreport(self):
        report_name = self.MatchReport()
        if report_name:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base_dir, 'report_template', report_name)
            tpl = DocxTemplate(path)
            print(report_name)

            # MSI图
            if self.data['msi'] and 'img_path' in self.data['msi'].keys() and self.data['msi']['img_path'] and os.path.exists(self.data['msi']['img_path']):
                self.data['msi'] = InlineImage(tpl, self.data['msi']['img_path'], width=Mm(100))
            # TMB图
            if self.data['tmb'] and 'img_path' in self.data['tmb'].keys() and os.path.exists(self.data['tmb']['img_path']):
                self.data['tmb']['img_path'] = InlineImage(tpl, self.data['tmb']['img_path'], width=Mm(100))
            # GEP图
            if self.data["gep"] and "img_path" in self.data["gep"].keys() and self.data["gep"]["img_path"] and os.path.exists(self.data["gep"]["img_path"]):
                self.data["gepplot"] = InlineImage(tpl, self.data["gep"]["img_path"], width=Mm(80))
            elif self.data["qc"] and "rna_data_qc" in self.data["qc"].keys() and self.data["qc"]["rna_data_qc"] and "gepplot" in self.data["qc"]["rna_data_qc"].keys() \
                and self.data["qc"]["rna_data_qc"]["gepplot"] and os.path.exists(self.data["qc"]["rna_data_qc"]["gepplot"]):
                self.data["gepplot"] = InlineImage(tpl, self.data["qc"]["rna_data_qc"]["gepplot"], width=Mm(80))
            # CNV图
            if re.search("Pan116（组织）|LC76（组织）|CRC25（组织）|GA18（组织）|TC21（组织）", self.data["sample"]["prod_names"]) and re.search("rummage", report_name):
                if "cnv_file_path" in self.data.keys() and self.data["cnv_file_path"] and "abs_path" in self.data["cnv_file_path"].keys() and self.data["cnv_file_path"]["abs_path"] \
                    and os.path.exists(self.data["cnv_file_path"]["abs_path"]):
                    tpl.replace_pic("test_MSI.png", self.data["cnv_file_path"]["abs_path"])


            # TME图
            if self.data["qc"] and "rna_data_qc" in self.data["qc"].keys() and self.data["qc"]["rna_data_qc"] and "tmeplot" in self.data["qc"]["rna_data_qc"].keys() and self.data["qc"]["rna_data_qc"]["tmeplot"] \
                and os.path.exists(self.data["qc"]["rna_data_qc"]["tmeplot"]):
                self.data["tmeplot"] = InlineImage(tpl, self.data["qc"]["rna_data_qc"]["tmeplot"], width=Mm(80))
            # PD-L1图
            if self.data["pdl1"] and "file_pdl1" in self.data["pdl1"].keys() and os.path.exists(self.data["pdl1"]["file_pdl1"]):
                tpl.replace_pic("test_PDL1.jpg", self.data["pdl1"]["file_pdl1"])

            tpl.render(self.data)
            tpl.save(self.output_div + '/' + self.json_name + '.docx')
        else:
            print('未匹配到报告模板')


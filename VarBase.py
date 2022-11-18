#-*- coding:utf-8 -*-
import copy
from ToolsBase import ToolsBase
import os
import re
import datetime
import itertools
from functools import reduce
import xlrd

'''
脚本描述：
    用来实现报告脚本的基本功能
    
'''

class VarBase(ToolsBase):
    def __init__(self, json_name, output_div):
        super().__init__(json_name, output_div)
        pass
        '''
        self.json_name = json_name
        self.data_js = json.load(open(os.path.join(output_div, json_name + '.json'), 'r', encoding='utf-8'))
        self.output_div = output_div
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        '''

    def Content(self, filepath):
        file = []
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                file.append(line)
        return file

    # 样本信息
    def sample_info(self):
        data = self.data_js['sample_info']
        data['report_date'] = str(datetime.date.today())
        for k, v in data.items():
            if not v:
                data[k] = ''
        # 新增日期格式，年月日，x/x/x
        receive_date = re.split('-', data['receive_data'])
        data['receive_date_special_1'] = receive_date[0] + '年' + receive_date[1] + '月' + receive_date[2] + '日' \
        if receive_date and len(receive_date) >= 3 else ''
        data['receive_date_special_2'] = receive_date[0] + '/' + receive_date[1] + '/' + receive_date[2] if receive_date \
            and len(receive_date) >= 3 else ''
        report_date = re.split('-', data['report_date'])
        data['report_date_special_1'] = report_date[0] + '年' + report_date[1] + '月' + report_date[2] + '日' if report_date \
            and len(report_date) >= 3 else ''
        data['report_date_special_2'] = report_date[0] + '/' + report_date[1] + '/' + report_date[2] if report_date and \
            len(report_date) >= 3 else ''

        # 新增生信分析时间
        json_name_list = re.split('_', data['json_batch_name'])
        json_date = json_name_list[0] if json_name_list else ''
        data['json_date'] = json_date[:4] + '年' + json_date[4:6] + '月' + json_date[6:] + '日' if json_date and len(json_date) == 8 else ''

        # 区分厦门和上海样本
        data['locate'] = 'SH' if re.match('S', data['sample_id']) else 'XM'

        # 肿瘤细胞含量新增数值字段，便于比对
        data['tumor_content_num'] = data['tumor_content'].replace('%', '') if 'tumor_content' in data.keys() and data['tumor_content'] else ''

        return data
    
    # 获取QC
    def getQC(self):
        # 判断是否是数值
        def is_number(i):
            try:
                float(i)
                return True
            except:
                pass
            if i.isnumeric():
                return True
            return False
        def QCStran_dict(qcDict):
            QC_result = {}
            for k, v in qcDict.items():
                if k != 'qc_type' and v:
                    QC_result[k+'_num'] = v if re.search('cleandata_size', k) else float(v) if is_number(v) else v
                    QC_result[k] = '{:.2%}'.format(float(v)) if re.search('q30|q20|ratio|uni20', k) else v if re.search('cleandata_size', k) \
                        else '{:.2f}'.format(float(v)) if is_number(v) else v
                else:
                    QC_result[k+'_num'] = 0
                    QC_result[k] = ''
            return QC_result
        def QCStran_list(qclist):
            QC_result = {}
            for i in qclist:
                QC_result.setdefault(i['qc_type'], {})
                for k, v in i.items():
                    if k != 'qc_type' and v:
                        QC_result[i['qc_type']][k+'_num'] = v if re.search('cleandata_size', k) else float(v)
                        QC_result[i['qc_type']][k] = '{:.2%}'.format(float(v)) if re.search('q30|q20|ratio|uni20', k) else v \
                            if re.search('cleandata_size', k) else '{:.2f}'.format(float(v))
                    else:
                        QC_result[i['qc_type']][k+'_num'] = 0
                        QC_result[i['qc_type']][k] = ''	
            return QC_result

        qc = self.data_js['qc']
        qc_items = [i for i in qc]
        data = {}
        for item in qc_items:
            # qc_gradient单独处理
            if item == 'qc_gradient' and qc['qc_gradient']:
                data['qc_gradient'] = {}
                for i in qc['qc_gradient']:
                    data['qc_gradient'][i['qc_source']+'_'+i['gradient_num']] = '{:.2%}'.format(float(i['gradient_ratio']))
            else:
                if type(qc[item]).__name__ == 'dict':
                    data[item] = QCStran_dict(qc[item])
                else:
                    if len(qc[item]) == 1:
                        data[item] = QCStran_dict(qc[item][0])
                    elif len(qc[item]) >= 2:
                        qc_data = reduce(lambda x, y : x if y in x else x + [y], [[],] + qc[item])
                        if len(qc_data) == 1:
                            data[item] = QCStran_dict(qc_data[0])
                        else:
                            data[item] = QCStran_list(qc[item])
        
        qc_lib = self.data_js['lib_quality_control'] if 'lib_quality_control' in self.data_js.keys() and self.data_js['lib_quality_control'] else {}
        qc_lib_items = [i for i in qc_lib]
        lib_data = {}
        for item in qc_lib_items:
            if type(qc_lib[item]).__name__ == 'dict':
                lib_data[item] = QCStran_dict(qc_lib[item][0])
            else:
                if len(qc_lib[item]) == 1:
                    lib_data[item] = QCStran_dict(qc_lib[item][0])
                elif len(qc_lib[item]) >= 2:
                    qc_data = reduce(lambda x, y:x if y in x else x + [y], [[],]+qc_lib[item])
                    if len(qc_data) == 1:
                        lib_data[item] = QCStran_dict(qc_data[0])
                    else:
                        lib_data[item] = QCStran_list(qc_lib[item])
        return data, lib_data
    
    # GEP
    def getGEP(self):
        gep_dict = self.data_js['gep']
        return gep_dict
    
    
    # 获取获批药物
    def getDrug(self):
        rule = self.getDrugSortRule()
        drug_list = self.data_js['drug']
        drug_result = []
        for drug in drug_list:
            drug['name'] = drug['general_name_cn'] if drug['general_name_cn'] else drug['general_name_en']
            if drug['var']:
                for a in drug['var']:
                    if a and 'hgvs_p' in a.keys() and a['hgvs_p']:
                        a['hgvs_p'] = a['hgvs_p'].replace('p.', 'p.(') + ')' if not re.search('=', a['hgvs_p'])\
                            and a['hgvs_p'] != 'p.?' else a['hgvs_p']
                    # MLPA的var统一格式，gene exon del/dup
                    if 'biomarker_type' in a.keys() and a['biomarker_type'] and re.search('BRCA', a['biomarker_type']) and \
                        re.search('Loss|Gain', a['biomarker_type']):
                        biomarker_type = re.split(':', a['biomarker_type'])
                        a['biomarker_type'] = biomarker_type[1] + ' ' + biomarker_type[2] + ' del' if 'Loss' in biomarker_type \
                            else biomarker_type[1] + ' ' + biomarker_type[2] + ' dup'
            # FDA和NMPA获批药物
            drug['approval_organization'] = list(set(drug["approval_organization"]) & set(["FDA", "NMPA"]))
            # 适应症去重
            adaptation = list(itertools.chain(*[re.split('\n', i.strip()) for i in drug['adaptation_disease_cn']])) \
                if drug['adaptation_disease_cn'] else []
            if str(drug['name']) in rule and drug['approval_organization'] and drug['var']:
                drug_result.append(drug)
        drug_result = sorted(drug_result, key=lambda i:rule.index(i['name']))

        return drug_result
   
    # 治疗方案信息
    def getRegimen(self):
        rule = self.getRegimenSortRule()
        regimen_list = self.data_js['therapeutic_regimen'] if 'therapeutic_regimen' in self.data_js.keys() else []
        regimen_result = []
        # 关于TMB-H相关药物，在不同医院和产品中释放规则不同，不应在基类中直接删除
        for regimen in regimen_list:
            if 'var' in regimen.keys() and regimen['var']:
                for a in regimen['var']:
                    if a and 'hgvs_p' in a.keys() and a['hgvs_p']:
                        a['hgvs_p'] = a['hgvs_p'].replace('p.', 'p.(') + ')' if not re.search('=', a['hgvs_p']) and a['hgvs_p'] != 'p.?' else a['hgvs_p']
                    # 将MLPA的var统一为gene exon del/gene exon dup
                    if 'biomarker_type' in a.keys() and a['biomarker_type'] and re.search('BRCA', a['biomarker_type']) and \
                        re.search('Loss|Gain', a['biomarker_type']):
                        biomarker_type = re.split(':', a['biomarker_type'])
                        a['biomarker_type'] = biomarker_type[1] + '' + biomarker_type[2] + ' del' if 'Loss' in biomarker_type else \
                            biomarker_type[1] + ' ' + biomarker_type[2] + ' dup'
            regimen['name'] = regimen['regimen_cn'] if regimen['regimen_cn'] else regimen['regimen_en']
            # 适应症拆分去重
            adaptation = list(itertools.chain(*[re.split('\n', i.strip()) for i in regimen['adaptation_disease_cn']])) if \
                regimen['adaptation_disease_cn'] else []
            regimen['adaptation_disease_cn'] = reduce(lambda x, y : x if y in x else x + [y], [[],] + adaptation)
            if str(regimen['name']) in rule and regimen['approval_organization'] and ('FDA' in regimen['approval_organization'] \
                or 'NMPA' in regimen['approval_organization']) and 'var' in regimen.keys() and regimen['var']:
                regimen_result.append(regimen)
        regimen_result = sorted(regimen_result, key=lambda i:rule.index(i['name']))

        # 融合格式调整，gene1:region1-gene2:region2
        for regimen in regimen_result:
            if 'var' in regimen.keys() and regimen['var']:
                for var in regimen['var']:
                    if var and 'hgvs' in var.keys() and var['hgvs'] and re.search('-', var['hgvs']):
                        five_prime_cds = '-'.join(re.split('-', (re.split(':', var['hgvs'])[2]))[:-1]) if not re.search('--', var['hgvs']) \
                            else re.split('_', (re.split('--', var['hgvs'])[0]))[-1]
                        three_prime_cds = re.split(':', var['hgvs'])[-1] if not re.search('--', var['hgvs']) \
                            else re.split('_', (re.split('--', var['hgvs'])[1]))[-1]
                        five_prime_gene = re.split(":", var["hgvs"])[0] if not re.search("--", var["hgvs"]) \
                            else re.split(":", (re.split("--", var["hgvs"])[0]))[0]
                        three_prime_gene = re.split(":", re.split("-", var["hgvs"])[-1])[0] if not re.search("--", var["hgvs"]) \
                            else re.split(":", (re.split("--", var["hgvs"])[1]))[0]
                        var["hgvs2"] = five_prime_gene+":"+five_prime_cds+"-"+three_prime_gene+":"+three_prime_cds+" 融合"
                    if 'gene_symbol' in var.keys() and var['gene_symbol']:
                        if ',' in var['gene_symbol']:
                            five_gene = re.split(',', var['gene_symbol'])[0]
                            three_gene = re.split(',', var['gene_symbol'])[1]
                            var['sv'] = five_gene + '-' + three_gene
        # 单药适应症用drug中的证据，联合用药用治疗方案中的证据
        drug_adapation = {}
        drug_trade_names = {}
        drug_info = self.data_js['drug'] if 'drug' in self.data_js.keys() else []
        for drug in drug_info:
            drug_name = drug["general_name_cn"].strip() if drug["general_name_cn"] else drug["general_name_en"].strip() if drug["general_name_en"] else ""
            adaptation = list(itertools.chain(*[re.split("\n", i.strip()) for i in drug["adaptation_disease_cn"]])) if drug["adaptation_disease_cn"] else []
            drug_adapation[drug_name] = {
                "adaptation_disease_cn" : reduce(lambda x, y:x if y in x else x + [y], [[],]+adaptation),
                "approval_organization" : drug["approval_organization"] if drug["approval_organization"] else []
            }
            drug_trade_names[drug_name] = {
                'trade_name_cn': drug['trade_name_cn'].strip() if drug['trade_name_cn'] else '',
                'trade_name_en': drug['trade_name_en'].strip() if drug['trade_name_en'] else ''
            }
        # 治疗方案单药适应症更新
        for regimen in regimen_result:
            if len(regimen['drug_details']) == 1:
                regimen_name = regimen['regimen_cn'].strip() if regimen['regimen_cn'] else regimen['regimen_en'].strip() if regimen['regimen_en'] else ''
                regimen["adaptation_disease_cn"] = drug_adapation[regimen_name]["adaptation_disease_cn"] if regimen_name in drug_adapation.keys() else regimen["adaptation_disease_cn"]
                regimen["approval_organization"] = drug_adapation[regimen_name]["approval_organization"] if regimen_name in drug_adapation.keys() else regimen["approval_organization"]
                regimen['trade_name_cn'] = drug_trade_names[regimen_name]['trade_name_cn'] if regimen_name in drug_trade_names.keys() else ''
                regimen['trade_name_en'] = drug_trade_names[regimen_name]['trade_name_en'] if regimen_name in drug_trade_names.keys() else ''
        return regimen_result
    
    # 相同证据描述的合并治疗方案展示
    def merge_Predictive_evi(self, datainfo):
        merge_result = []
        if datainfo:
            tmp_dict = {}
            for evi in datainfo:
                tmp_dict.setdefault(evi['evi_interpretation'],  [])
                tmp_dict[evi['evi_interpretation']].append({
                    'regimen_name' : evi['regimen_name'],
                    'evi_conclusion_simple' : evi['evi_conclusion_simple'],
                    'clinical_significance_cn' : evi['clinical_significance_cn'],
                    'regimen_name_py' : evi['regimen_name_py']
                })
            
            for k, v in tmp_dict.items():
                merge_result.append({
                    'regimen_name' : '、'.join([i['regimen_name'] for i in v]),
                    'evi_conclusion_simple' : '/'.join([i['evi_conclusion_simple'] for i in v]),
                    'clinical_significance_cn' : '/'.join([i['clinical_significance_cn'] for i in v]),
                    'regimen_name_py' : '/'.join([i['regimen_name_py'] for i in v]),
                    'evi_interpretation' : k
                })
        return merge_result
    
    # 处理变异对应的治疗方案
    def varRegimen(self, evi_sum):
        data = {}
        data['refer_evi'] = []
        data['evi_split'] = {}
        for evi in evi_sum:
            evi['clinical_significance_cn'] = self.senseTrans().get(evi['clinical_significance'], evi['clinical_significance'])
            evi['evi_conclusion_simple'] = evi['evi_conclusion'][0] if evi['evi_conclusion'] else ''
            # 证据描述去掉末尾空格
            evi['evi_interpretation'] = evi['evi_interpretation'].strip() if evi['evi_interpretation'] else ''
            # Predictive证据，非治疗的放前面
            evi['regimen_name_py'] = self.topinyin(evi['regimen_name']) if evi['regimen_name'] else '0'
            # 用于排敏感、耐药的字段
            evi['sense_rule'] = '0' if re.search('Sensitive', evi['clinical_significance']) else '1' if \
                re.search('Resistant', evi['clinical_significance']) else evi['clinical_significance']
        
        evi_sum = sorted(evi_sum, key = lambda i:(i["evi_conclusion_simple"], i["sense_rule"], i["regimen_name_py"].upper()))
        for evi in evi_sum:
            data['refer_evi'].extend(self.getRef_from_inter(evi['evi_interpretation']))
            if evi['evidence_type'] not in data['evi_split'].keys():
                data['evi_split'].setdefault(evi['evidence_type'], [])
            data['evi_split'][evi['evidence_type']].append(evi)

            if 'Predictive' in data['evi_split'].keys():
                data["evi_split"]["Predictive_merge"] = self.merge_Predictive_evi(data["evi_split"]["Predictive"])
        data["regimen_evi_sum"] = evi_sum
        data["regimen_FDA_S"] = [{"regimen_name" : var["regimen_name"], "evi_conclusion_simple" : var["evi_conclusion_simple"]} \
            for var in evi_sum if re.search("Sensitive",var["clinical_significance"]) and var["evi_conclusion_simple"] == "A"]
        data["regimen_noFDA_S"] = [{"regimen_name" : var["regimen_name"], "evi_conclusion_simple" : var["evi_conclusion_simple"]} \
            for var in evi_sum if re.search("Sensitive",var["clinical_significance"]) and var["evi_conclusion_simple"] != "A"]
        data["regimen_S"] = [{"regimen_name" : var["regimen_name"], "evi_conclusion_simple" : var["evi_conclusion_simple"]} \
            for var in evi_sum if re.search("Sensitive",var["clinical_significance"])]
        data["regimen_R"] = [{"regimen_name" : var["regimen_name"], "evi_conclusion_simple" : var["evi_conclusion_simple"]} \
            for var in evi_sum if re.search("Resistant",var["clinical_significance"])]
        
        return data

    # 处理变异，特殊要求不在base中实现
    # 处理变异等级,后续snvindel、cnv、sv复用
    def process_var_level(self, var):
        var['clinic_num_g'] = self.clinicalNumStran().get(var['clinical_significance'], 3)
        var['clinic_num_s'] = self.functionNumStran().get(var['function_classification'], 3)
        if var['evi_sum']:
            var['evi_sum'] = self.varRegimen(var['evi_sum'])
            
        
        regimen_level = [i["evi_conclusion_simple"] for i in var["evi_sum"]["regimen_evi_sum"] if i["evidence_type"] in ["Predictive", "Prognostic", "Diagnostic"]] \
            if var['evi_sum'] and 'regimen_evi_sum' in var['evi_sum'].keys() else []
        var['clinic_num_s'] = 5 if set(['A', 'B']) & set(regimen_level) else 4 if var['clinic_num_s'] in [4, 5] else var['clinic_num_s']
        var['top_level'] = 'A' if 'A' in regimen_level else 'B' if 'B' in regimen_level else 'C' if 'C' in regimen_level else 'D' if 'D' in regimen_level else 'N'

        return var
    
    # 处理SNVINDEL
    def process_snvindel(self):
        snvindel = self.data_js['snvindel']
        for var in snvindel:
            # 默认格式，hgvs_p加括号，hgvs_p_abbr加括号
            var['hgvs_p'] = var["hgvs_p"].replace("p.", "p.(")+")" if not re.search("=", var["hgvs_p"]) and \
                var["hgvs_p"] != "p.?" else var["hgvs_p"]
            var["hgvs_p_abbr"] = var["hgvs_p_abbr"] if var["hgvs_p_abbr"] else ""
            var["hgvs_p_abbr"] = var["hgvs_p_abbr"].replace("p.", "p.(")+")" if var["hgvs_p_abbr"] and not re.search("=", var["hgvs_p_abbr"]) \
                and var["hgvs_p_abbr"] != "p.?" else var["hgvs_p_abbr"]
            
            var["freq_ss"] = var["freq_ss"] if var["freq_ss"] else var["freq_case"]
            var["freq_str"] = "{:.2%}".format(float(var["freq"])) if var["freq"] else ""
            var["freq_ss_str"] = "{:.2%}".format(float(var["freq_ss"])) if var["freq_ss"] else ""
            var["transcript_primary_simple"] = re.split("\.", str(var["transcript_primary"]))[0] if var["transcript_primary"] else ""
            var["type_cn"] = self.typeStran().get(var["type"], var["type"])
            # 手动新增的变异，变异类型可能为空
            var["type_cn"] = var["type_cn"] if var["type_cn"] else ""
            
            var = self.process_var_level(var)
            # 三字母氨基酸为为空，用报告脚本转化的结果
            var["hgvs_p_abbr"] = self.splitAA(var["hgvs_p"]) if not var["hgvs_p_abbr"] else var["hgvs_p_abbr"]
        snvindel = sorted(snvindel, key=lambda i:i['freq'], reverse=True)
        
        return snvindel
    
    # 处理CNV
    def process_cnv(self):
        cnv = self.data_js['cnv']
        for var in cnv:
            var['cn_mean'] = format(round(float(var['cn_mean']), 2) + 0.00, '.2f') if 'cn_mean' in var.keys() and var['cn_mean'] else 0
            var = self.process_var_level(var)
        cnv = sorted(cnv, key=lambda i:float(i['cn_mean']), reverse=True)

        return cnv
    
    # 处理SV
    # 合并DNA RNA共检
    def matchRNA_DNA_SV(self, sv, rna_sv):
        rna_sv_dict = {}
        for var in rna_sv:
            rna_sv_dict.setdefault(var['five_prime_gene'] + ':' + var['five_prime_cds'] + '-' + var['three_prime_gene'] + ':' + var['three_prime_cds'], {})
            rna_sv_dict[var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"]] = var
        
        rna_sv_only = copy.deepcopy(rna_sv)
        rna_sv_pop_key = []
        for var in sv:
            if var['five_prime_gene']+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"] in rna_sv_dict.keys():
                var["rna_detect"] = rna_sv_dict[var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"]]
                rna_sv_pop_key.append(var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"])
        # 匹配完的，rna_sv_only把DNA/RNA共检变异删掉
        for var in rna_sv_only:
            if var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"] in rna_sv_pop_key:
                rna_sv_only.remove(var)
        
        return sv, rna_sv_only

    def process_sv(self):
        sv = self.data_js['sv']
        rna_sv = self.data_js['rna_sv']
        # sv
        for var in sv:
           var = self.process_var_level(var)
           var['five_prime_cds'] = "-".join(re.split("-", (re.split(":", var["var_hgvs"])[2]))[:-1]) if not re.search("--", var["var_hgvs"]) else re.split("_", (re.split("--", var["var_hgvs"])[0]))[-1]
           var["three_prime_cds"] = re.split(":", var["var_hgvs"])[-1] if not re.search("--", var["var_hgvs"]) else re.split("_", (re.split("--", var["var_hgvs"])[1]))[-1]
           tmp_dict = {var["five_prime_gene"] : var["five_prime_transcript"], var["three_prime_gene"] : var["three_prime_transcript"]}
           var["transcript_primary"] = tmp_dict.get(var["gene_symbol"], "")
           var["freq_str"] = "{:.2%}".format(float(var["freq"])) if "freq" in var.keys() and var["freq"] else ""
           var["copies"] = var["copies"] if "copies" in var.keys() and var["copies"] else ""
        
        # rna sv
        for var in rna_sv:
            var = self.process_var_level(var)
            var["five_prime_cds"] = re.split(":", var["five_prime_cds"])[0]
            var["three_prime_cds"] = re.split(":", var["three_prime_cds"])[0]
            var["freq"] = int(float(var["supp_splt_reads"]) + float(var["supp_span_reads"]))
        
        sv_match, rna_sv_only = self.matchRNA_DNA_SV(sv, rna_sv)
        sv_match = sorted(sv_match, key=lambda i:float(str(i["freq"]).replace("%","")), reverse=True)
        rna_sv = sorted(rna_sv, key=lambda i:float(i["freq"]), reverse=True)
        rna_sv_only = sorted(rna_sv_only, key=lambda i:float(i["freq"]), reverse=True)

        return sv_match, rna_sv, rna_sv_only
    
    def process_knb(self):
        knb = self.data_js['knb'][0] if self.data_js['knb'] else {}
        if knb:
            knb['evi_sum'] = self.varRegimen(self.data_js, knb['evi_sum'])
        
        return knb
    
    def process_ga_type(self, var_data):
        ga_result = {}
        ebv_gene_list = ['PIK3CA', 'ARID1A', 'BCOR']
        gs_gene_list =['CDH1', 'RHOA', 'CLDN18']
        cin_gene_list = ['TP53', 'ERBB2', 'KRAS', 'EGFR', 'CDK6', 'CCNE1', 'APC', 'CTNNB1', 'SMAD2', 'SMAD4', 'PTEN']
        ebv_type_dict = self.ListToDict(self.data_js['ebv_type']) if 'ebv_type' in self.data_js.keys() and self.data_js['ebv_type'] else {}
        # 胃癌分子分型有：EBV、MSI、GS、CIN四种，胃癌分子分型相关标志物部分检测到的分型都展示
        # 检测小结部分
        # 检测到EBV、MSI则展示EBV、MSI（同时存在则都展示）
        # 未检测到EBV、MSI时，若存在GS、CIN分型，则展示（同时存在则都展示）
	    ### 变异未限定变异类型
	    # 展示体细胞I/II/肿瘤发生发展相关变异和胚系致病/疑似致病变异
        level_12_var = [var for var in var_data if (var['var_origin'] != 'germline' and var['clinic_num_s'] in [5, 4] or (var['var_origin'] == 'germline' and var['clinic_num_g'] in [5, 4]))]
        def get_var(gene_list):
            result_dict = {}
            result_list = []
            for var in level_12_var:
                for gene in re.split(',', var['gene_symbol']):
                    if gene in gene_list:
                        if gene not in result_dict.keys():
                            result_dict.setdefault(gene, [])
                        var_info = '扩增' if var['bio_category'] == 'Cnv' else var['five_prime_gene']+'-'+var['three_prime_gene']+'融合' if var['bio_category'] in ['Sv', 'PSeqRnaSv'] else var['hgvs_p'] \
                        if var['bio_category'] == 'Snvindel' and var['hgvs_p'] != 'p.?' else var['hgvs_c'] if var['bio_category'] == 'Snvindel' and var['hgvs_p'] == 'p.?' else ''
                        result_dict[gene].append(var_info)
                        result_list.append(gene + ' ' + var_info)
                    
            return result_dict, ', '.join(result_list)

        ebv_gene_result, ebv_gene_str = get_var(ebv_gene_list)
        gs_gene_list, gs_gene_str = get_var(gs_gene_list)
        cin_gene_list, cin_gene_str = get_var(cin_gene_list)
        ga_result = {
            'ebv_type' : ebv_type_dict,
            'ebv_gene' : ebv_gene_result,
            'ebv_sum' : ebv_gene_str,
            'gs_gene' : gs_gene_list,
            'gs_sum' : gs_gene_str,
            'cin_gene' : cin_gene_list,
            'cin_sum' : cin_gene_str
        }

        return ga_result
    
    def process_mlpa(self):
        mlpa = self.data_js['mlpa']
        result = {}
        for var in mlpa:
            var['evi_sum'] = self.varRegimen(var['evi_sum']) if 'evi_sum' in var.keys() and var['evi_sum'] else []
        for gene in ['BRCA1', 'BRCA2']:
            for i in ['Loss', 'Gain']:
                result['B' + gene[-1] + '_' + i] = [var for var in mlpa if var['gene_symbol'] == gene  and re.search(i, var['type'])]
        
        return result

    def process_ec_type(self):
        ec_type_dict = self.ListToDict(self.data_js['ec_type'])
        ec_type_dict['evi_sum'] = self.varRegimen(ec_type_dict['evi_sum'])

        return ec_type_dict
    
    def getTMB(self):
        tmb_dict = self.ListToDict(self.data_js['tmb'])
        if "evi_sum" in tmb_dict.keys() and tmb_dict["evi_sum"]:
            tmb_dict["evi_sum"] = self.varRegimen(tmb_dict["evi_sum"])
        
        return tmb_dict

    def getTME(self):
        tme_dict = self.ListToDict(self.data_js['tme_type']) if 'tme_type' in self.data_js.keys() else {}
        tme_score = self.data_js['tme_score'] if 'tme_score' in self.data_js.keys() else {}
        if tme_score:
            for k, v in tme_score.items():
                tme_score[k] = '{:.2f}'.format(float(v))
        
        return tme_dict, tme_score
    
    def getPDL1(self):
        pdl1_dict = self.ListToDict(self.data_js['pdl1'])
        if pdl1_dict:
            pdl1_dict['value'] = str(int(float(pdl1_dict['value']) * 100)) + '%' if pdl1_dict['result'] == '阳性' and pdl1_dict['type'] == 'TPS' else int(pdl1_dict['value']) if \
                pdl1_dict['result'] == '阳性' and pdl1_dict['type'] == 'CPS' else pdl1_dict['value']
        
        return pdl1_dict

    def getchemo(self):
        chemo_data = self.data_js['PGx']
        chemo_result = {}
        chemo_reduce = [{'gene_symbol' : i['gene_symbol'], 'dbsnp' : i['dbsnp'], 'genotype' : i['genotype'], 'clin_anno_cn' : i['clin_anno_cn'], 'evi_level' : i['evi_level']} for i in chemo_data]
        chemo_reduce = reduce(lambda x, y : x if y in x else x + [y], [[], ] + chemo_reduce)
        # 返回一个完整版，一个去重版的化疗内容，其他特殊处理可在定制化脚本里实现
        chemo_result['complete'] = sorted(chemo_data, key=lambda i : (i['gene_symbol'], i['dbsnp']))
        chemo_result['reduce_116'] = sorted(chemo_reduce, key=lambda i:(i['gene_symbol'], i['dbsnp']))

        return chemo_result
    
    def getRNAExp(self):
        rna_exp_data = self.data_js['rna_exp']
        rna_exp = {}

        def process_data(rna_exp_data, num):
            rna_exp = []
            for i in range(0, len(rna_exp_data)-num, num):
                tmp_dict = {}
                for j in range(1, num+1):
                    tmp_dict["gene"+str(j)] = rna_exp_data[i+j-1]["gene_symbol"]
                    tmp_dict["tpm"+str(j)] = rna_exp_data[i+j-1]["tpm"]
                rna_exp.append(tmp_dict)
            
            rest_gene = len(rna_exp_data) % num
            rest_tmp_dict = {}
            for j in range(1, num+1):
                rest_tmp_dict['gene' + str(j)] = ''
                rest_tmp_dict['tpm' + str(j)] = ''
            rest_num = 1
            if rest_gene != 0:
                for j in range(len(rna_exp_data) - rest_gene - num, len(rna_exp_data)):
                    rest_tmp_dict["gene"+str(rest_num)] = rna_exp_data[j]["gene_symbol"]
                    rest_tmp_dict["tpm"+str(rest_num)] = rna_exp_data[j]["tpm"]
                    rest_num += 1
                rna_exp.append(rest_tmp_dict)
            else:
                for j in range(len(rna_exp_data)-rest_gene-num, len(rna_exp_data)):
                    rest_tmp_dict["gene"+str(rest_num)] = rna_exp_data[j]["gene_symbol"]
                    rest_tmp_dict["tpm"+str(rest_num)] = rna_exp_data[j]["tpm"]
                    rest_num += 1
                rna_exp.append(rest_tmp_dict)
            return rna_exp
        
        if rna_exp_data:
            rna_exp['column_4'] = process_data(rna_exp_data, 4)
            rna_exp['column_5'] = process_data(rna_exp_data, 5)
        
        return rna_exp
    
    def getMSI(self):
        msi_dict = self.ListToDict(self.data_js['msi'])
        if msi_dict:
            msi_dict['msi_num_cp40'] = int(float(msi_dict['msi_score']) * 55 + 0.5) if msi_dict['msi_score'] or msi_dict['msi_score'] == 0 else ''
        if 'evi_sum' in msi_dict.keys() and msi_dict['evi_sum']:
            msi_dict['evi_sum'] = self.varRegimen(self.data_js, msi_dict['evi_sum'])
        
        return msi_dict
    
    def getClinic(self):
        clinic_list = self.data_js['clinic_trial']
        gene_list = []
        result = []

        def stran_druginfo(druginfo):
            regimen_dict = {
                'Drug' : '_Drug',
                "Biological" : "_Biological",
                "Procedure" : "_Procedure",
                "Other" : "_Other",
                "Device" : "_Device",
                "Behavioral" : "_Behavioral",
                "Radiation" : "_Radiation",
                "Diagnostic Test" : "_Diagnostic Test",
                "Genetic" : "_Genetic"
            }

            for k, v in regimen_dict.items():
                if k in druginfo:
                    druginfo = druginfo.replace(k, v)
            return druginfo
        
        for i in clinic_list:
            if i['gene_symbol'] not in gene_list:
                gene_list.append(i['gene_symbol'])
        
        for gene in gene_list:
            clinic_cn = [i for i in clinic_list if re.search('CTR', i['clinicaltrial_number']) and i['gene_symbol'] == gene]
            clinic_en = [i for i in clinic_list if re.search('NCT', i['clinicaltrial_number']) and i['gene_symbol'] == gene and 'Drug' in i['interventions']]

            if clinic_cn:
                clinic_cn = sorted(clinic_cn, key=lambda i : i['phase'])
                for i in clinic_cn:
                    i['interventions'] = [i['interventions']]
                result += clinic_cn if len(clinic_cn) <= 3 else clinic_cn[0:3]
            
            phase_dict = {
                "Phase 1" : "I期",
                "Phase 2" : "II期",
                "Phase 3" : "III期",
                "Phase 4" : "IV期",
                "Phase 1 Phase 2" : "I期/II期",
                "Phase 2 Phase 3" : "II期/III期",
                "Early Phase 1" : "Early I期"
            }
            if clinic_en:
                clinic_en = sorted(clinic_en, key=lambda i : i['phase'], reverse=True)
                for i in clinic_en:
                    druginfo = stran_druginfo(i['interventions'])
                    druglist = []
                    for j in re.split('_', druginfo):
                        j = j.replace('Drug: ', '')
                        druglist.append(j)
                    i['interventions'] = druglist
                    i['phase'] = phase_dict.get(i['phase'], '')
                result += clinic_en if len(clinic_en) <= 3 else clinic_en[0:3]
        return result
    
    # 不同panel的io相关基因也不同，可以改成灵活的列表，这样可以复用代码
    def io_detect(self, var_data):
        io_result = {}
        io_p_result = ''
        io_n_result = ''
        io_gene_P = ["ATM","ATR","BRCA1","BRCA2","BRIP1","CHEK1","CHEK2","ERCC1","FANCA","MRE11","PALB2","RAD50","XRCC1","MLH1","MSH2","MSH6","PMS2","POLE","POLD1","TP53","KRAS",
        "CD274","ARID1A","LRP1B","SETD2","PRKDC","TERT","KMT2D","FAT1","CDK12","SERPINB3","SERPINB4"]
        io_gene_N = ["EGFR","ALK","MDM2","MDM4","CDKN2A","CDKN2B","DNMT3A","STK11","IFNGR1","IRF1","JAK1","JAK2","APC","CTNNB1","B2M","PTEN","CCND1","FGF3","FGF4","FGF19"]
        level_12_var = [var for var in var_data if (var['var_origin'] != 'germline' and var['clinic_num_s'] in [5, 4]) or (var['var_origin'] == 'germline' and var['clinic_num_g'] in [5, 4])]
        for var in level_12_var:
            if var['bio_category'] == 'Cnv' and var['gene_symbol'] in ['CD274', 'MDM2', 'MDM4', 'CCND1', 'FGF3', 'FGF4', 'FGF19']:
                if var['gene_symbol'] not in io_result.keys():
                    io_result.setdefault(var['gene_symbol'], [])
                io_result[var['gene_symbol']].append('扩增')
            elif var['bio_category'] in ['Sv', 'PSeqRnaSv'] and set(re.split(',', var['gene_symbol'])) and set(['ALK']):
                if 'ALK' not in io_result.keys():
                    io_result.setdefault('ALK', [])
                io_result["ALK"].append(var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"]+"融合")
            elif var["bio_category"] == "Snvindel" and var["gene_symbol"] in io_gene_P + io_gene_N:
                if var["gene_symbol"] not in io_result.keys():
                    io_result.setdefault(var["gene_symbol"], [])
                if var["hgvs_p"] != "p.?":
                    io_result[var["gene_symbol"]].append(var["hgvs_p"])
                else:
                    io_result[var["gene_symbol"]].append(var["hgvs_c"])
        # summary展示
        io_p_list = []
        io_n_list = []
        for k, v in io_result.items():
            if k not in ['CCND1', 'FGF3', 'FGF4', 'FGF19']:
                for i in v:
                    if k in io_gene_P:
                        io_p_list.append(k + ' ' + i)
                    elif k in io_gene_N:
                        if not re.search('融合', i):
                            io_n_list.append(k + ' ' + i)
                        else:
                            io_n_list.append(i)
        if "CCND1" in io_result.keys() and "FGF3" in io_result.keys() and "FGF4" in io_result.keys() and "FGF19" in io_result.keys():
            io_n_list.append("CCND1/FGF3/FGF4/FGF19扩增")
        num = len(io_p_list + io_n_list)
        io_p_result = ", ".join(io_p_list)
        io_n_result = ", ".join(io_n_list)

        return io_result, io_p_result, io_n_result, num

    def mergeVar(self, var_data):
        judge_MET14 = []
        judge_METSV = []
        for var in var_data:
            if var['bio_category'] in ['Sv', 'PSeqRnaSv'] and var['five_prime_gene'] == 'MET' and var['three_prime_gene'] == 'MET' and var['evi_sum']['evi_split'] and \
                'Predictive' in var['evi_sum']['evi_split']:
                judge_METSV = var
                METSV_regimen = [(i['regimen_name'], i['evi_conclusion']) for i in var['evi_sum']['evi_split']['Predictive']]
        if judge_METSV:
            for var in var_data:
                regimen = [(i["regimen_name"], i["evi_conclusion"]) for i in var["evi_sum"]["evi_split"]["Predictive"]] if var['clinc_num_s'] in [4, 5] and var['evi_sum']['evi_split'] \
                    and 'Predictive' in var['evi_sum']['evi_split'] else []
                if var['bio_category'] == 'Snvindel' and var['gene_symbol'] == 'MET' and regimen == METSV_regimen:
                    judge_MET14 = var
                    var_data.remove(var)
                    var_data.remove(judge_METSV)
                    judge_MET14['hgvs_p_2'] = 'MET-MET融合'
                    judge_MET14['freq_2'] = str(judge_METSV['copies']) + ' copies' if 'copies' in judge_METSV.keys() else str(int(judge_MET14['reads'])) + ' copies' if \
                        'reads' in judge_METSV.keys() else ''
                    judge_MET14['judge_mergeMET'] = 'yes'
        if judge_MET14:
            var_data.insert(0, judge_MET14)
        
        return var_data
    
    def getHRD(self, BRCA_data):
        hrd_dict = self.ListToDict(self.data_js['hrd'])
        if "evi_sum" in hrd_dict.keys() and hrd_dict["evi_sum"]:
            # HRD治疗方案转化
            hrd_dict['evi_sum'] = self.varRegimen(self.data_js, hrd_dict['evi_sum'])
            # HRD治疗方案汇总
            regimen_sum = [{'regimen_name' : i['regimen_name'], 'evidence_type' : i['evidence_type'], 'clinical_significane_cn' : i['clinical_significance_cn'], 
            'evi_conclusion_simple' : i['evi_conclusion_simple'], 'regimen_name_py' : i['regimen_name_py']} for i in hrd_dict['evi_sum']['regimen_evi_sum']]
            # BRCA治疗方案汇总
            if BRCA_data:
                for var in BRCA_data:
                    regimen_sum += [{"regimen_name":i["regimen_name"], "evidence_type":i["evidence_type"], "clinical_significance_cn":i["clinical_significance_cn"], 
                    "evi_conclusion_simple":i["evi_conclusion_simple"],"regimen_name_py":i["regimen_name_py"]} for i in var["evi_sum"]["regimen_evi_sum"]]
            
            regimen_sum_redup = []
            for i in regimen_sum:
                if i not in regimen_sum_redup:
                    regimen_sum_redup.append[i]
            regimen_sum_redup = sorted(regimen_sum_redup, key=lambda i : (i["evi_conclusion_simple"], i["clinical_significance_cn"], i["regimen_name_py"]))
            # 等级判断
            regimen_level = [i['evi_conclusion_simple'] for i in regimen_sum_redup]
            hrd_dict['level_num'] = 5 if set(['A', 'B']) & set(regimen_level) else 4 if set(['C', 'D']) & set(regimen_level) else 3
            # 治疗方案分类展示
            hrd_dict['regimen'] = {}
            for regimen in regimen_sum_redup:
                if regimen['evidence_type'] not in hrd_dict['regimen']:
                    hrd_dict['regimen'].setdefault(regimen['evidence_type'], [])
                hrd_dict['regimen'][regimen['evidence_type']].append(regimen)
        
        return hrd_dict
    
    def Master_sum(self, var_data):
        result = s_var_rule(var_data)

        def var_count(var_list):
            num = 0
            for var in var_list:
                num += 1
                if 'rna_detect' in var.keys():
                    num += 1
            return num
        
        return var_count(result["level_I"]), var_count(result["level_II"]), var_count(result["level_onco_nodrug"]), var_count(result["level_III"])


    # 格式化配置文件
    def stran_xlrd(self, sheet_name):
        fixed_refer_path = os.path.join(self.BASE_DIR, 'config/reference.xlsx')
        xls = xlrd.open_workbook(fixed_refer_path)
        refer_sheet = xls.sheet_by_name(sheet_name)
        key = refer_sheet.row_values(0)
        Data = []
        for num in range(1, refer_sheet.nrows):
            rows = refer_sheet.row_values(num)
            tmpdict = {}
            for i in range(len(key)):
                tmpdict[key[i]] = rows[i]
            Data.append(tmpdict)

        return Data
    
    # 固定问下格式处理
    def stran_fixed_refer(self, i):
        authors = i['authors'].split(',')
        if len(authors) > 3:
            i['authors'] = ','.join([authors[0], authors[1], authors[2], 'et al.'])
        if i['date']:
            i['date'] = '(' + re.search(r'\d{4}', str(i["date"]).replace(".0", "")).group(0) + ')'
        if i['title']:
            i['title'] = i['title'].strip('.') + '.'
        if i['PMID']:
            i['PMID'] = ''.join(['[', 'PMID:', str(int(i['PMID'])), ']'])
        result = " ".join([i["authors"], i["date"], i["title"], i["journal"], i["vol"], i["PMID"]])

        return result
    
    def getdynamic_refer(self, var_data, hrd):
        dynamic_refer = {}
        msi = self.getMSI()

        # 默认参考文献
        # 1. s_var12：获取基因介绍、变异解读、治疗、诊断、预后、遗传风险参考文献，包含I/II类
        dynamic_refer["s_var12"] = []
        for var in var_data["var_somatic"]["level_I"] + var_data["var_somatic"]["level_II"]:
            dynamic_refer["s_var12"].extend(self.getRef_from_inter(var["gene_function"]))
            dynamic_refer["s_var12"].extend(self.getRef_from_inter(var["variant_interpret_cn"]))
            dynamic_refer["s_var12"].extend(var["evi_sum"]["refer_evi"])
        # 2. s_var_onco_nodrug 获取基因介绍、变异解读，包含肿瘤发生发展相关变异
        dynamic_refer["s_var_onco_nodrug"] = []
        for var in var_data["var_somatic"]["level_onco_nodrug"]:
            dynamic_refer["s_var_onco_nodrug"].extend(self.getRef_from_inter(var["gene_function"]))
            dynamic_refer["s_var_onco_nodrug"].extend(self.getRef_from_inter(var["variant_interpret_cn"]))
        # 3. s_var3：获取基因介绍、变异解读，包含III类变异
        dynamic_refer["s_var3"] = []
        for var in var_data["var_somatic"]["level_III"]:
            dynamic_refer["s_var3"].extend(self.getRef_from_inter(var["gene_function"]))
            dynamic_refer["s_var3"].extend(self.getRef_from_inter(var["variant_interpret_cn"]))
        # 4. g_var12: 获取基因介绍、变异解读、治疗、诊断、预后、遗传风险参考文献
        dynamic_refer["g_var45"] = []
        for var in var_data["var_germline"]["level_4"] + var_data["var_germline"]["level_5"]:
            dynamic_refer["g_var45"].extend(self.getRef_from_inter(var["gene_function"]))
            dynamic_refer["g_var45"].extend(self.getRef_from_inter(var["variant_interpret_cn"]))
            dynamic_refer["g_var45"].extend(var["evi_sum"]["refer_evi"])
        # 5. g_var3: 获取基因介绍、变异解读
        dynamic_refer["g_var3"] = []
        for var in var_data["var_germline"]["level_3"]:
            dynamic_refer['g_var3'].extend(self.getRef_from_inter(var['gene_function']))
            dynamic_refer["g_var3"].extend(self.getRef_from_inter(var["variant_interpret_cn"]))
        # 6. KNB：获取KNB阴性时的治疗、诊断、预后、遗传风险参考文献
        dynamic_refer["knb"] = var_data["knb"]["evi_sum"]["refer_evi"] if var_data["knb"] else []
        # 7. EC：EC分型临床辅助治疗决策
        dynamic_refer["ec_type"] = var_data["ec_type"]["evi_sum"]["refer_evi"] if var_data["ec_type"] and "evi_sum" in var_data["ec_type"].keys() else []
        # 8. MSI：MSI-H时的治疗策略
        dynamic_refer["msi"] = msi["evi_sum"]["refer_evi"] if msi and msi["var_id"] == "MSI-H" else []
        # 9. HRD：治疗策略
        dynamic_refer["hrd"] = hrd["evi_sum"]["refer_evi"] if hrd and hrd["evi_sum"] else []

        return dynamic_refer
    
    def getfixed_refer(self, report_name, tumor_list):
        # 固定参考文献
        # 涵盖胃癌分子分型，GEP，TME
        msi = self.getMSI()
        knb = self.process_knb()
        Data = self.stran_xlrd('reference-fixed')
        fixed_refer = []
        refer_type_dict = {}
        for i in [refer for refer in Data if refer['docx_template'] == report_name]:
            refer_type_dict.setdefault(i['refer_type'], [])
            refer_type_dict[i['refer_type']].append(i)
        # 1. fixed：固定参考文献直接展示
        if "fixed" in refer_type_dict.keys():
            fixed_refer += refer_type_dict["fixed"]
        # 2. tumor: 只匹配癌种
        if "tumor" in refer_type_dict.keys():
            for refer in refer_type_dict["tumor"]:
                if refer["tumor_or_type"] in tumor_list:
                    fixed_refer.append(refer)
        # 3. tumor_and_result: 匹配癌种和结果，目前有4种
        if "tumor_and_result" in refer_type_dict.keys():
            for refer in refer_type_dict["tumor_and_result"]:
                if refer['tumor_or_type'] == 'KNB' and knb:
                    fixed_refer.append(refer)
                if "肺癌" in tumor_list and refer["tumor_or_type"] == "GEP":
                    fixed_refer.append(refer)
                if "肺癌" in tumor_list and refer["tumor_or_type"] == "TME":
                    fixed_refer.append(refer)
        # 4. result ： 仅匹配结果，目前有1种
        if "result" in refer_type_dict.keys():
            for refer in refer_type_dict["result"]:
                # 4.1. MSI-H
                if refer["tumor_or_type"] == "MSI-H" and msi["var_id"] == "MSI-H":
                    fixed_refer.append(refer)
        fixed_refer_stran = [self.stran_fixed_refer(i) for i in fixed_refer]

        return fixed_refer_stran
    
    def getgss(self, var_data):
        result = {}
        result['gss'] = self.ListToDict(self.data_js['gss']) if 'gss' in self.data_js.keys() and self.data_js['gss'] else {}
        for gene in ['BRCA1', 'BRCA2']:
            result[gene] = [var for var in var_data if ((var["clinic_num_s"] in [4, 5] and var["var_origin"] != "germline") or 
            (var["clinic_num_g"] in [4, 5] and var["var_origin"] == "germline")) and var["gene_symbol"] == gene]
        # HRR 通路基因检测结果
        filepath = os.path.join(self.BASE_DIR, 'config/HRR_gene.txt')
        gene_list = self.Content(filepath)
        hrr_result = [var for var in var_data if ((var["clinic_num_s"] in [4, 5] and var["var_origin"] != "germline") or (var["clinic_num_g"] in [4, 5] and var["var_origin"] == "germline")) 
        and set(re.split(",", var["gene_symbol"])) & set(gene_list)]
        result["summary"] = ''
        hrr_list = []
        # HRD阳性判断
        for var in hrr_result:
            if var["bio_category"] == "Snvindel":
                if var["hgvs_p"] != "p.?":
                    hrr_list.append(var["gene_symbol"] + " " + var["hgvs_p"])
                else:
                    hrr_list.append(var["gene_symbol"] + " " + var["hgvs_c"])
            elif var["bio_category"] == "Cnv":
                hrr_list.append(var["gene_symbol"] + " 扩增")
            elif var["bio_category"] in ["Sv", "PSeqRnaSv"]:
                hrr_list.append(var["five_prime_gene"]+":"+var["five_prime_cds"]+"-"+var["three_prime_gene"]+":"+var["three_prime_cds"]+" 融合")
        result["summary"] = ", ".join(hrr_list)

        return result
    
    def process_var(self):
        snvindel = self.process_snvindel()
        cnv = self.process_cnv()
        sv_combination, rna_sv, rna_sv_only = self.process_sv()
        if re.search('Pan116|LC76', self.data_js['sample_info']['prod_names']):
            for var in snvindel:
                if var['gene_symbol'] == 'BCL2L11' and var['hgvs_c'] and var['hgvs_c'] == 'c.394+1479_394+4381del':
                    snvindel.remove(var)
        # 通用变异排序
        rule = {"Snvindel" : 0, "Cnv" : 1, "Sv" : 2, "PSeqRnaSv" : 3}
        top_level_rule = {"A" : 0, "B" : 1, "C" : 2, "D" : 3, "N" : 4}
        var_data_without_rnasv = sorted(snvindel + cnv + sv_combination, key=lambda i : (i["clinic_num_s"], top_level_rule.get(i["top_level"]), i["gene_symbol"], rule.get(i["bio_category"])))
        var_data_rna_sv = sorted(rna_sv, key=lambda i : (i["clinic_num_s"], top_level_rule.get(i["top_level"]), i["gene_symbol"], rule.get(i["bio_category"])))
        var_data = sorted(snvindel + cnv + sv_combination + rna_sv_only, key=lambda i : (i["clinic_num_s"], top_level_rule.get(i["top_level"]), i["gene_symbol"], rule.get(i["bio_category"])))
        # 合并MET 14跳读
        var_data_without_rnasv = self.mergeVar(var_data_without_rnasv)
        var_data = self.mergeVar(var_data)

        return var_data, var_data_without_rnasv, var_data_rna_sv


    def getVar(self):
        '''
        这部分可以根据项目进行删减，免得生成的中间数据很大，在排查报告问题的时候中间json文件不方便查看
        '''
        data = {}
        var_data, var_data_without_rnasv, var_data_rna_sv = self.process_var()
        # 体细胞变异结果整理
        
        data["var_somatic_without_rnasv"] = s_var_rule(var_data_without_rnasv)
        data["var_somatic_rna_sv"] = s_var_rule(var_data_rna_sv)
        data["var_somatic"] = s_var_rule(var_data)
        # 胚系结果整理
        data["var_germline"] = {**g_var_rule(var_data), **g_var_regimen_rule(var_data)}
        # 胚系+体细胞有用药建议/预后/辅助诊断变异整理
        data["var_for_regimen"] = var_regimen_rule(var_data)
        data["var_for_regimen_without_rnasv"] = var_regimen_rule(var_data_without_rnasv)
        

        data['knb'] = self.process_knb()
        data["ec_type"] = {}
        if self.data_js['ec_type']:
            data['ec_type'] = self.process_ec_type(self.data_js)
            if data["ec_type"]["evi_sum"]["evi_split"] and "Prognostic" in data["ec_type"]["evi_sum"]["evi_split"].keys():
                data["ec_type"]["clinical_significance"] = [i["clinical_significance"] for i in data["ec_type"]["evi_sum"]["evi_split"]["Prognostic"]]
                data["ec_type"]["evi_interpretation"] = "".join([i["evi_interpretation"] for i in data["ec_type"]["evi_sum"]["evi_split"]["Prognostic"]])
        # TP53、POLE、BRCA1、BRCA2基因检测结果，分为I/II类和III类，用于变异和分子分型分开展示的情况
        ec_gene_list = ["TP53", "POLE", "BRCA1", "BRCA2"]
        for gene in ec_gene_list:
            data["ec_type"].update(var_bptm_rule(var_data, gene))
        
        data["mlpa"] = self.process_mlpa()
        data['GA_type'] = self.process_ga_type(var_data)
        data['gss'] = self.getgss(var_data)

        data['BCL2L11'] = ''
        for var in self.data_js['snvindel']:
            if var["gene_symbol"] == "BCL2L11" and var["hgvs_c"] == "c.394+1479_394+4381del":
                data["BCL2L11"] = "T"
                break
        # LC10需展示未检到I/II类变异的基因
        lc10_gene = ["BRAF", "EGFR", "ERBB2", "KRAS", "MET", "ALK", "ROS1", "RET", "NRAS", "PIK3CA"]
        data["lc10_withoutPathVar_geneList"] = nofoundPath_genelist(var_data, lc10_gene)
        # LC10临检通用模板展示未检测到I/II/III类变异的基因
        data["lc10_withoutVar_geneList"] = nofound_genelist(var_data, lc10_gene)
        # CRC12-MSI需要展示未检测到I/II类变异的基因
        crc12_gene = ["KRAS", "NRAS", "BRAF", "POLE", "PIK3CA", "ERBB2", "ALK", "FGFR3", "NTRK1", "NTRK3", "RET"]
        data["crc12_withoutPathVar_geneList"] = nofoundPath_genelist(var_data, crc12_gene)
        # 胚系-林奇综合征：五个基因结果需要分开展示（EPCAM、MLH1、MSH2、MSH6、PMS2）
        # 展示上述基因的3、4、5类变异
        gLS5_gene_list = ["EPCAM", "MLH1", "MSH2", "MSH6", "PMS2"]
        data["gLS5"] = var_lyn5_rule(var_data, gLS5_gene_list)

        # 免疫正负相关
        data["io"] = {}
        data["io"]["result"], data["io"]["io_p_summary"], data["io"]["io_n_summary"], data['io']['num'] = self.io_detect()

        return data
    
    def getNCCN_detect(self, var_data):
        # 用于MP临检通用、浙肿MP和CP40，NCCN指南推荐基因
        snvindel_gene = ["EGFR", "KIT", "PDGFRA","BRCA1","BRCA2","ATM","BARD1","BRIP1","CDH1","CDK12","CHEK1","CHEK2","FANCA","FANCL","HDAC2","PALB2","PPP2R2A","PTEN","RAD51B","RAD51C","RAD51D","RAD54L","TP53", "ERBB2"]
        snv_gene = ["ALK", "ROS1", "RET", "BRAF", "ERBB2", "PIK3CA", "FGFR2", "FGFR3", "IDH1", "IDH2"]
        fusion_gene = ["ALK", "ROS1", "RET", "FGFR2", "FGFR3", "NTRK1", "NTRK2", "NTRK3"]
        cnv_gene = ["MET", "ERBB2"]
        other_gene = ["MET", "KRAS", "NRAS"]
        result = {}
        # 只展示I/II/肿瘤发生发展变异和胚系4/5类变异
        level_12_var = [var for var in var_data if (var["clinic_num_s"] in [5, 4] and var["var_origin"] != "germline") or (var["clinic_num_g"] in [5, 4] and  var["var_origin"] == "germline")]
        for i in level_12_var:
            var_info = "扩增" if i["bio_category"] == "Cnv" else i["five_prime_gene"]+"-"+i["three_prime_gene"]+"融合" if i["bio_category"] == "Sv" or i["bio_category"] == "PSeqRnaSv" else \
                i["hgvs_p"] if i["hgvs_p"]!="p.?" else i["hgvs_c"]
            var_info2_sv = i["five_prime_gene"]+":"+i["five_prime_cds"]+"-"+i["three_prime_gene"]+":"+i["three_prime_cds"]+"融合" if i["bio_category"] == "Sv" or i["bio_category"] == "PSeqRnaSv" else ""
            if i["bio_category"] == "Sv":
                freq = str(i["rna_detect"]["freq"])+" copies" if "rna_detect" in i.keys() and i["rna_detect"] else i["freq_str"]
            else:
                freq = i["cn_mean"] if i["bio_category"] == "Cnv" else i["freq_str"] if i["bio_category"] == "Snvindel" else str(i["freq"])+" copies"
            
            if i["bio_category"] == "Snvindel" and i["gene_symbol"] in snvindel_gene:
                if i["gene_symbol"]+"_snvindel" not in result.keys():
                    result.setdefault(i["gene_symbol"]+"_snvindel", [])
                result[i["gene_symbol"]+"_snvindel"].append({"var_info" : var_info, "freq" : freq})
            
            if i["bio_category"] == "Snvindel" and i["gene_symbol"] in snv_gene and not re.search("del|ins|fs", i["hgvs_p"]):
                if i["gene_symbol"]+"_snv" not in result.keys():
                    result.setdefault(i["gene_symbol"]+"_snv", [])
                result[i["gene_symbol"]+"_snv"].append({"var_info" : var_info, "freq" : freq})
            
            if i["bio_category"] == "Cnv" and i["gene_symbol"] in cnv_gene:
                if i["gene_symbol"]+"_cn" not in result.keys():
                    result.setdefault(i["gene_symbol"]+"_cn", [])
                result[i["gene_symbol"]+"_cn"].append({"var_info" : var_info, "freq" : freq})
            
            if i["bio_category"] in ["Sv", "PSeqRnaSv"] and set(re.split(",", i["gene_symbol"])) & set(fusion_gene):
                for sv_gene in set(re.split(",", i["gene_symbol"])):
                    if sv_gene+"_sv" not in result.keys():
                        result.setdefault(sv_gene+"_sv", [])
                    result[sv_gene+"_sv"].append({"var_info" : var_info, "freq" : freq, "var_info_M" : var_info2_sv})
            
            # 特殊检测内容处理
            # KRAS、NRAS 分为G12|G13|Q61|A146和其他变异
            if i["bio_category"] == "Snvindel" and i["gene_symbol"] in ["KRAS", "NRAS"]:
                if re.search("G12|G13|Q61|A146", i["hgvs_p"]):
                    if i["gene_symbol"]+"_sp" not in result.keys():
                        result.setdefault(i["gene_symbol"]+"_sp", [])
                    result[i["gene_symbol"]+"_sp"].append({"var_info" : var_info, "freq" : freq})
                else:
                    if i["gene_symbol"]+"_ot" not in result.keys():
                        result.setdefault(i["gene_symbol"]+"_sp", [])
                    result[i["gene_symbol"]+"_sp"].append({"var_info" : var_info, "freq" : freq})
            
            # MET 14跳跃突变
            if i["gene_symbol"] == "MET" and i["bio_category"] == "Snvindel" and (i["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(i["evi_sum"]["evi_split"].keys()) \
                and i["clinic_num_s"] == 5) or ("judge_mergeMET" in i.keys() and i["judge_mergeMET"]):
                if "MET_skip" not in result.keys():
                    result.setdefault("MET_skip", [])
                result["MET_skip"].append({"var_info" : var_info, "freq" : freq})
            if i["bio_category"] in ["Sv", "PSeqRnaSv"] and i["five_prime_gene"] == "MET" and i["three_prime_gene"] == "MET":
                if "MET_skip" not in result.keys():
                    result.setdefault("MET_skip", [])
                result["MET_skip"].append({"var_info" : var_info, "freq" : freq})
        
        sort_result = {}
        for k, v in result.items():
            sort_result[k] = []
            for i in v:
                if i not in sort_result[k]:
                    sort_result[k].append(i)
        
        return result

# 各类排序、筛选规则
def s_var_rule(var_data):
    '''
    体细胞变异分为I/II/肿瘤发生发展相关/III类-不分基因 适用于大部分模板
    '''
    result = {'level_I' : [], 'level_II' : [], 'level_onco_nodrug' : [], 'level_III' : []}
    if var_data:
        for var in var_data:
            
            if var['clinic_num_s'] == 5 and var['var_origin'] != 'germline' and 'evi_sum' in var.keys() and var['evi_sum']['evi_split'] and set(['Diagnostic', 'Predictive', 'Prognostic']) & set(var['evi_sum']['evi_split'].keys()):
                result['level_I'].append(var)
            elif var['clinic_num_s'] == 4 and var['var_origin'] != 'germline' and 'evi_sum' in var.keys() and var['evi_sum']['evi_split'] and set(['Diagnostic', 'Predictive', 'Prognostic']) & set(var['evi_sum']['evi_split'].keys()):
                result["level_II"].append(var)
            elif var['clinic_num_s'] in [5, 4] and var['var_origin'] != 'germline' and (('evi_sum' in var.keys() and not var['evi_sum']['evi_split']) or \
                ('evi_sum' in var.keys() and var['evi_sum']['evi_split'] and not set(['Diagnostic', 'Predictive', 'Prognostic']) & set(var['evi_sum']['evi_split'].keys()))):
                result["level_onco_nodrug"].append(var)
            elif var['clinic_num_s'] == 3 and var['var_origin'] != 'germline':
                result['level_III'].append(var)

    return result

def s_var_rule_gene(var_data, gene):
    '''
    体细胞变异分为I/II/肿瘤发生发展相关/III类-分单个基因 适用于PTM、BPTM和部分定制模板
    注意：融合变异主基因可能存在“gene1,gene2”的格式
    '''
    result = {}
    result["level_I"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set([gene]) and var["clinic_num_s"] == 5 and var["var_origin"] != "germline" and "evi_sum" in var.keys() 
    and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]

    result["level_II"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set([gene]) and var["clinic_num_s"] == 4 and var["var_origin"] != "germline" and "evi_sum" in var.keys() 
    and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]

    result["level_onco_nodrug"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set([gene]) and var["clinic_num_s"] in [5, 4] and var["var_origin"] != "germline" 
    and (("evi_sum" in var.keys() and not var["evi_sum"]["evi_split"]) or ("evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and not set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())))]

    result["level_III"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set([gene]) and var["clinic_num_s"] == 3 and var["var_origin"] != "germline"]

    return result

def s_var_rule_genelist(var_data, genelist):
    result = {}
    result["level_I"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set(genelist) and var["clinic_num_s"] == 5 and var["var_origin"] != "germline" 
    and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]

    result["level_II"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set(genelist) and var["clinic_num_s"] == 4 and var["var_origin"] != "germline" 
    and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]

    result["level_onco_nodrug"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set(genelist) and var["clinic_num_s"] in [5, 4] and var["var_origin"] != "germline" 
    and (("evi_sum" in var.keys() and not var["evi_sum"]["evi_split"]) or ("evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and not set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())))]

    result["level_III"] = [var for var in var_data if set(re.split(",", var["gene_symbol"])) & set(genelist) and var["clinic_num_s"] == 3 and var["var_origin"] != "germline"]

    return result

def g_var_rule(var_data):
	'''
	胚系分为5/4/3/2/1类
	'''
	result = {}
	for i in range(1, 6):
		result["level_"+str(i)] = [var for var in var_data if var["clinic_num_g"] == i and var["var_origin"] == "germline"]
	return result

def g_var_rule_genelist(var_data, genelist):
	'''
	胚系分为5/4/3/2/1类，并匹配基因列表
	'''
	result = {}
	for i in range(1, 6):
		result["level_"+str(i)] = [var for var in var_data if var["clinic_num_g"] == i and var["var_origin"] == "germline" and var["gene_symbol"] in genelist]
	return result

def g_var_regimen_rule(var_data):
	'''
	胚系变异根据治疗/辅助诊断/预后证据提取I/II类
	'''
	result = {}
	result["regimen_level_I"] = [var for var in var_data if var["clinic_num_s"] == 5 and var["var_origin"] == "germline" and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]
	result["regimen_level_II"] = [var for var in var_data if var["clinic_num_s"] == 4 and var["var_origin"] == "germline" and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]
	return result

def var_regimen_rule(var_data):
	'''
	胚系+体细胞变异根据治疗/辅助诊断/预后证据提取I/II类
	'''
	result = {}
	result["level_I"] = [var for var in var_data if var["clinic_num_s"] == 5 and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]
	result["level_II"] = [var for var in var_data if var["clinic_num_s"] == 4 and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())]
	return result

def process_result_regimen_ZJZL(var_list_zjzl):
	'''
	浙江肿瘤胚系+体细胞有用药建议/预后/辅助诊断变异整理（报告中仅展示用药，无用药且有预后/辅助诊断的写“暂无靶向用药提示”，模板代码中较难实现，故这边再加字段）

	'''
	for var in var_list_zjzl:
		if "Predictive" not in var["evi_sum"]["evi_split"]:
			var["evi_sum"]["evi_split"]["Predictive"] = {"note" : "without_regimen"}
	return var_list_zjzl

def var_bptm_rule(var_data, gene):
	'''
	PTM/BPTM需要展示各个基因的情况，因为TP53、POLE、BRCA基因都有证据，不存在肿瘤发生发展相关变异，有的话，可以在这边改。
	'''
	result = {}
	# 格式1：I/II、III类
	result[gene+"_level12"] = [var for var in var_data if var["clinic_num_s"] in [5, 4] and var["var_origin"] != "germline" and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys()) and var["gene_symbol"] == gene]
	result[gene+"_level3"] = [var for var in var_data if var["clinic_num_s"] ==3 and var["var_origin"] != "germline" and var["gene_symbol"] == gene]
	# 格式2：与格式1区别在于如果未检出变异，需要标记
	result[gene+"_level12_withECtype"] = copy.deepcopy(result[gene+"_level12"]) if result[gene+"_level12"] else [{"gene_symbol" : gene, "result" : "nofound"}]
	result[gene+"_level3_withECtype"] = copy.deepcopy(result[gene+"_level3"]) if result[gene+"_level3"] else [{"gene_symbol" : gene, "result" : "nofound"}]
	# 格式3：I/II/III结果放一起
	level_data = s_var_rule_gene(var_data, gene)
	result[gene+"_withEC_type"] = level_data["level_I"] + level_data["level_II"] + level_data["level_onco_nodrug"] + level_data["level_III"]
	result[gene+"_withEC_type"] = result[gene+"_withEC_type"] if result[gene+"_withEC_type"] else [{"gene_symbol" : gene, "result" : "nofound"}]

	return result

def var_lyn5_rule(var_data, gene_list):
	'''
	胚系-林奇综合征：五个基因结果需要分开展示（EPCAM、MLH1、MSH2、MSH6、PMS2）
	展示上述基因的3、4、5类变异
	'''
	result = {}
	for gene in gene_list:
		if gene not in result.keys():
			result.setdefault(gene, [])
		result[gene] = [var for var in var_data if var["clinic_num_g"] in [5, 4, 3] and var["var_origin"] == "germline" and var["gene_symbol"] == gene]
	return result

def nofoundPath_genelist(var_data, gene_list):
	'''
	提取未检测到I/II类体细胞变异的基因
	'''
	return sorted(list(set(gene_list) - set([var["gene_symbol"] for var in var_data if var["clinic_num_s"] in [4,5] and var["var_origin"] != "germline" and "evi_sum" in var.keys() and var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys())])))

def nofound_genelist(var_data, gene_list):
	'''
	提取未检测到体细胞变异的基因(包含I/II/III/肿瘤发生发展相关)
	'''
	return sorted(list(set(gene_list) - set([var["gene_symbol"] for var in var_data if var["clinic_num_s"] in [3,4,5] and var["var_origin"] != "germline"])))

def S_level(var):
	'''
	致病/疑似致病但无用药的变异，在结果汇总表中归为III类
	'''
	s_level = var["clinic_num_s"] if var["evi_sum"]["evi_split"] and set(["Diagnostic","Predictive","Prognostic"]) & set(var["evi_sum"]["evi_split"].keys()) else 3
	return s_level

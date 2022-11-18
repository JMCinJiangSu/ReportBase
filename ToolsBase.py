#-*- coding:utf-8 -*-

from itertools import chain
import json
import os
import sys
import re
from pypinyin import pinyin, Style
import xlrd

class ToolsBase:
    def __init__(self, json_name, output_div):
        '''
        传入的json不需要后缀
        '''
        if not os.path.exists(output_div):
            os.makedirs(output_div)
        self.json_name = json_name
        self.data_js = json.load(open(os.path.join(output_div, json_name + '.json'), 'r', encoding='utf-8'))
        self.output_div = output_div
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.requirenment_path = os.path.join(self.BASE_DIR, 'config/report_requirenment.xlsx')
    
    # 药物先后顺序制定成排序规则,选择用药敏感的药物
    def getDrugSortRule(self):
        rule = []
        var_list = self.data_js['snvindel'] + self.data_js['cnv'] + self.data_js['sv'] + self.data_js['rna_sv'] + \
            self.data_js['knb'] + self.data_js['msi'] + self.data_js['tmb'] + self.data_js['pdl1'] + self.data_js['mlpa']
        drug_list = []
        for var in var_list:
            if 'evi_sum' in var.keys():
                drug_list += [evi['regimen_name'] for evi in var['evi_sum'] if evi['regimen_name'] and \
                    re.search('Sensitive', evi['clinical_significance'])] 
        for drug in drug_list:
            for i in re.split('\+', drug):
                if i.strip() not in rule:
                    rule.append(i.strip())
        return rule
    
    # 治疗方案排序规则
    def getRegimenSortRule(self):
        var_list = self.data_js['snvindel'] + self.data_js['cnv'] + self.data_js['sv'] + self.data_js['rna_sv'] + self.data_js['knb'] + self.data_js['msi'] + self.data_js['tmb'] + self.data_js['pdl1'] + self.data_js['mlpa']
        regimen_list = []
        for var in var_list:
            if type(var).__name__ == 'dict':
                if 'evi_sum' in var.keys():
                    for evi in var['evi_sum']:
                        if evi['regimen_name'] and re.search("Sensitive", evi["clinical_significance"]):
                            regimen_list.append(evi['regimen_name'])
                            #regimen_list += [evi["regimen_name"] for evi in var["evi_sum"] if evi["regimen_name"] and re.search("Sensitive", evi["clinical_significance"])]
        return regimen_list
    
    # 列表转字典
    def ListToDict(self, json_result):
        '''
        将MSI、PD-L1、TMB等应该为字典却输出为列表的信息转回字典，若有多个，则默认选择列表第一个元素
        '''
        return json_result if type(json_result).__name__ == 'dict' else json_result[0] if json_result else {}
    
    # 中文转拼音
    def topinyin(self, instr):
        return ''.join(chain.from_iterable(pinyin(instr, Style.TONE3)))
    
    # 氨基酸转换
    def splitAA(self, hgvs_p):
        transAA = {
        'A':'Ala',
		'C':'Cys',
		'D':'Asp',
		'E':'Glu',
		'F':'Phe',
		'G':'Gly',
		'H':'His',
		'I':'Ile',
		'K':'Lys',
		'L':'Leu',
		'M':'Met',
		'N':'Asn',
		'P':'Pro',
		'Q':'Gln',
		'R':'Arg',
		'S':'Ser',
		'T':'Thr',
		'V':'Val',
		'W':'Trp',
		'Y':'Tyr',
		'*':'Ter'
        }
        AA_str = []
        for i in list(hgvs_p):
            if i in transAA.keys():
                AA_str.append(transAA[i])
            else:
                AA_str.append(i)
            hgvs_p_abbr = ''.join(AA_str)
        
        return hgvs_p_abbr
    
    # 产品别名转换
    def alias_name(self):
        '''
        获取报告模板配置文件信息
        产品别名信息
        '''
        xls = xlrd.open_workbook(self.requirenment_path)
        requirenment_sheet = xls.sheet_by_name('prod_alias_name')
        key = requirenment_sheet.row_values(0)
        Data = {}
        for num in range(1, requirenment_sheet.nrows):
            rows = requirenment_sheet.row_values(num)
            Data[rows[0]] = rows[1]
        
        return Data
    
    # 获取配置文件信息
    def getfile(self, filepath):
        config_dict = json.loads(open(filepath, 'r', encoding='utf-8').read())
        return config_dict
    
    def clinicalNumStran(self):
        clinical_num_path = os.path.join(self.BASE_DIR, 'config/clinical_num_stran.json')
        return self.getfile(clinical_num_path)
    
    def functionNumStran(self):
        function_num_path = os.path.join(self.BASE_DIR, 'config/function_num_stran.json')
        return self.getfile(function_num_path)
    
    def senseTrans(self):
        sense_path = os.path.join(self.BASE_DIR, 'config/sense_stran.json')
        return self.getfile(sense_path)
    
    def typeStran(self):
        type_path = os.path.join(self.BASE_DIR, 'config/type_stran.json')
        return self.getfile(type_path)
    
    def evidenceTypeStran(self):
        evidenc_type_path = os.path.join(self.BASE_DIR, 'config/evidence_type_stran.json')
        return self.getfile(evidenc_type_path)
    
    # 获取报告模板配置
    def getRequirement(self):
        xls = xlrd.open_workbook(self.requirenment_path)
        requirenment_sheet = xls.sheet_by_name('report_requirenment')
        key = requirenment_sheet.row_values(0)
        key_stran = {
            '产品名称' : 'prod_name',
            '检测业务类型' : 'business_type',
            '模板类型' : 'report_type',
            '单位名称' : 'company',
            '科室' : 'hosp_depart',
            '模板名' : 'report_name',
	        '状态' : 'status',
	        '模板开发者' : 'developer',
	        '添加人' : 'auditors',
	        '添加时间' : 'auditors_time',
	        '备注' : 'note',
	        '更新记录' : 'update',
	        '临检' : 'clinical',
	        '进院' : 'hospital',
	        '定制' : 'CustomEdition',
	        '通用' : 'Universal',
	        '通用-简版' : 'Universal_simple',
	        '通用-完整' : 'Universal_complete'
        }
        Data = []
        for num in range(1, requirenment_sheet.nrows):
            rows = requirenment_sheet.row_values(num)
            tmpdict = {}
            for i in range(len(key)):
                tmpdict[key_stran.get(key[i])] = key_stran[rows[i]] if rows[i] in key_stran.keys() else rows[i]
            Data.append(tmpdict)
        
        requir_dict = {
            'clinical' : {
                'CustomEdition' : {},
                'Universal_simple' : {},
                'Universal_complete' : {}
            },
            'hospital' : {
                'CustomEdition' : {},
                'Universal' : {}
            }
        }
        
        for i in Data:
            if str(int(i['status'])) == '0':
                if i['company']:
                    if i['hosp_depart']:
                        requir_dict[i['business_type']][i['report_type']].setdefault((i['company'],i['hosp_depart'], i['prod_name']), '')
                        requir_dict[i['business_type']][i['report_type']][(i['company'], i['hosp_depart'], i['prod_name'])] = i['report_name']
                    else:
                        requir_dict[i['business_type']][i['report_type']].setdefault((i['company'], i['prod_name']), '')
                        requir_dict[i['business_type']][i['report_type']][(i['company'], i['prod_name'])] = i['report_name']
                else:
                    requir_dict[i['business_type']][i['report_type']].setdefault(i['prod_name'], '')
                    requir_dict[i['business_type']][i['report_type']][i['prod_name']] = i['report_name']
        return requir_dict
    
    # 选择报告模板
    def MatchReport(self):
        requir_dict = self.getRequirement()
        sample_info = self.data_js.get('sample_info')
        alias_name_dict = self.alias_name()
        sample_info['prod_names'] = alias_name_dict[sample_info['prod_names']] if sample_info['prod_names'] in alias_name_dict.keys() \
            else sample_info['prod_names']
        
        report_name = ''
        if sample_info['report_module_type'] == 'clinical':
            sample_info['origin_company'] = sample_info['origin_company'] if sample_info['origin_company'] else sample_info['company']
            if (sample_info['origin_company'], sample_info['prod_names']) in requir_dict['clinical']['CustomEdition'].keys():
                report_name = requir_dict['clinical']['CustomEdition'].get(sample_info['origin_company'], sample_info['prod_names'])
            else:
                report_name = requir_dict['clinical']['Universal_simple'].get(sample_info['prod_names'], '') if \
                    re.search('汇总', sample_info['origin_company']) else requir_dict['clinical']['Universal_complete'].get(sample_info['prod_names'], '')
        elif sample_info['report_module_type'] == 'hospital':
            if (sample_info['company'], sample_info['prod_names'], sample_info['hosp_depart']) in requir_dict['hospital']['CustomEdition'].keys():
                report_name = requir_dict['hospital']['CustomEdition'].get(sample_info['company'], sample_info['prod_names'], sample_info['hosp_depart'])
            elif (sample_info['company'], sample_info['prod_names']) in requir_dict['hospital']['CustomEdition'].keys():
                report_name = requir_dict['hospital']['CustomEdition'].get((sample_info['company'], sample_info['prod_names']))
            else:
                report_name = requir_dict['hospital']['Universal'].get(sample_info['prod_names'], '')
        
        return report_name
    
    # 氨基酸变异描述
    def AAstrans(self, hgvs_p, var_type):
        AA_dict = {
            'A' : '丙氨酸',
			'C' : '半胱氨酸',
			'D' : '天冬氨酸',
			'E' : '谷氨酸',
			'F' : '苯丙氨酸',
			'G' : '甘氨酸',
			'H' : '组氨酸',
			'I' : '异亮氨酸',
			'K' : '赖氨酸',
			'L' : '亮氨酸',
			'M' : '蛋氨酸',
			'N' : '天冬酰胺',
			'P' : '脯氨酸',
			'Q' : '谷氨酰胺',
			'R' : '精氨酸',
			'S' : '丝氨酸',
			'T' : '苏氨酸',
			'V' : '缬氨酸',
			'W' : '色氨酸',
			'Y' : '酪氨酸',
			'*' : '终止密码'
        }
        outstr = ''
        mat = re.compile(r'\d+')
        # 错义突变和无义突变
        if (var_type == 'nonSynonymous_Substitution' or var_type == 'Nonsense_Mutation') and not re.search('del|ins|dup', hgvs_p):
            pos_list = [i for i in mat.findall(hgvs_p)]
            hgvs_p_stran = [AA_dict[i] for i in list(hgvs_p) if i in AA_dict.keys()]
            outstr = '该突变导致基因编码蛋白第' + pos_list[0] + '位氨基酸由' + hgvs_p_stran[0] + '突变为' + hgvs_p_stran[-1]
        # 移码突变
        if re.search('fs*', hgvs_p):
            for i in mat.findall(re.split('fs\*', hgvs_p)[0]):
                pos = i
            endpos = int(pos) + int(re.split('fs\*', hgvs_p)[-1].replace(')', '')) - 1
            hgvs_p_stran = [AA_dict[i] for i in re.split('fs*', hgvs_p)[0] if i in AA_dict.keys()]
            outstr = '该突变导致基因编码蛋白第'+pos+'位氨基酸由'+hgvs_p_stran[0]+'突变为'+hgvs_p_stran[-1]+'并于'+str(endpos)+'位发生提前终止'
        # 延伸突变
        if var_type == 'Extension':
            pos_list = [i for i in mat.findall(hgvs_p)]
            hgvs_p_stran = [AA_dict[i] for i in re.split('ext', hgvs_p)[0].replace('*', '') if i in AA_dict.keys()]
            outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位终止密码突变为'+hgvs_p_stran[0]+'之后形成新的终止密码'
        # 非移码突变
        # 缺失
        if re.search('del', hgvs_p) and not re.search('delins', hgvs_p):
            pos_list = [i for i in mat.findall(hgvs_p)]
            hgvs_p_stran = [AA_dict[i] for i in hgvs_p if i in AA_dict.keys()]
            if len(pos_list) == 1:
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位氨基酸缺失'
            else:
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[-1]+'位氨基酸缺失'
        # 插入
        if re.search('ins', hgvs_p) and not re.search('delins', hgvs_p):
            pos_list = [i for i in mat.findall(re.split('ins', hgvs_p)[0])]
            insAA = re.split('ins', hgvs_p)[-1].replace(')','')
            if re.search('^[0-9]*$', insAA):
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[1]+'位氨基酸之间插入'+insAA+'个氨基酸'
            else:
                hgvs_p_stran = [AA_dict[i] for i in insAA if i in AA_dict.keys()]
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[1]+'位氨基酸之间插入'+'、'.join(hgvs_p_stran)
        # 重复
        if re.search('dup', hgvs_p):
            pos_list = [i for i in mat.findall(hgvs_p)]
            hgvs_p_stran = [AA_dict[i] for i in hgvs_p if i in AA_dict.keys()]
            if len(pos_list) == 1:
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位氨基酸重复'
            else:
                outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[1]+'位氨基酸重复'
        # 缺失插入
        if re.search('delins', hgvs_p):
            pos_list = [i for i in mat.findall(re.split('delins', hgvs_p)[0])]
            delinsAA = re.split('delins', hgvs_p)[-1].replace(')','')
            if len(pos_list) > 1:
                if re.search('^[0-9]*$', delinsAA):
                    outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[1]+'位氨基酸缺失并插入'+delinsAA+'个氨基酸'
                else:
                    hgvs_p_stran = [AA_dict[i] for i in delinsAA if i in AA_dict.keys()]
                    outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位到'+pos_list[1]+'位氨基酸缺失并插入'+'、'.join(hgvs_p_stran)
            else:
                if re.search('^[0-9]*$', delinsAA):
                    outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位氨基酸缺失并插入'+delinsAA+'个氨基酸'
                else:
                    hgvs_p_stran = [AA_dict[i] for i in delinsAA if i in AA_dict.keys()]
                    outstr = '该突变导致基因编码蛋白第'+pos_list[0]+'位氨基酸缺失并插入'+'、'.join(hgvs_p_stran)
        # 内含子突变
#        if var_type == 'Intronic' or var_type == 'Splicing':
#            outstr = '该突变可能造成异常剪接'
        return outstr
    
    # PMID 参考文献获取
    def getPMID_from_inter(self, inter):
        pmid_list = []
        mat = re.compile(r'PMID.\s?\d+')
        for i in mat.findall(str(inter)):
            if re.search(':|: |；|： ', i):
                pmid = (re.split(':|: |；|： ', i))[1].replace(' ', '')
            else:
                pmid = (re.split('PMID', i))[1]
            pmid_list.append(pmid)
        
        return pmid_list
    
    def getRef_from_json(self):
        ref_dict = {}
        for ref in self.data_js['refer']:
            pmid = re.split(':', ref['pmid'])[-1].replace(']', '')
            ref['authors'] = ref['authors'] if ref['authors'] else ''
            ref['date'] = ref['date'] if ref['date'] else ''
            ref['title'] = ref['title'] if ref['title'] else ''
            ref['journal'] = ref['journal'] if ref['journal'] else ''
            ref['vol'] = ref['vol'] if ref['vol'] else ''
            ref['pmid'] = ref['pmid'] if ref['pmid'] else ''
            ref_dict[pmid] = ' '.join([ref['authors'], ref['date'], ref['title'], ref['journal'], ref['vol'], ref['pmid']])
        
        return ref_dict
    
    def getRef_from_inter(self, inter):
        ref_dict = self.getRef_from_json()
        pmid_list = self.getPMID_from_inter(inter)
        refer_list = [ref_dict[i] for i in pmid_list if i in ref_dict.keys()]

        return refer_list


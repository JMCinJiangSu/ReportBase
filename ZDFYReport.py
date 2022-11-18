# -*- coding:utf-8 -*-

import argparse
import json
import re
import os
from ReportBase import ReportBase
from VarBase import VarBase, s_var_rule, s_var_rule_gene, g_var_rule, g_var_regimen_rule, var_bptm_rule, var_regimen_rule

class ZDFYReport(ReportBase):
    def __init__(self, json_name, output_div):
        super().__init__(json_name, output_div)
        pass

    def var_sum(self, var_data, tumor_names_cn):
        '''
        在小结出展示指南推荐检测基因的检测结果
        无推荐基因则展示实体瘤
        展示I级体细胞变异
        '''
        recom_path = os.path.join(self.BASE_DIR, "config/rpt_guideline_recom.json")
        with open(recom_path, "r", encoding='utf-8') as file_json:
            recomDict = json.load(file_json)
        
        recom_gene = [var["gene_symbol"] for var in recomDict["RECORDS"] if var["disease"] == tumor_names_cn or var["disease"] == "实体瘤"]
        recom_sum = []
        for var in var_data:
            if var['gene_symbol'] in recom_gene and (var['clinic_num_s'] in [5, 4] or var['clinic_num_g'] in [5, 4]):
                recom_sum.append(var)
        
        for i in recom_sum:
            try:
                recom_gene.remove(i['gene_symbol'])
            except:
                pass

        recom_gene = [{'gene_symbol' : i} for i in recom_gene]
        recom_sum.extend(recom_gene)
        for var in recom_sum:
            regimen_list_S = []
            regimen_list_R = []
            if "evi_sum" in var.keys() and var["evi_sum"]["regimen_FDA_S"]:
                for regimen in var["evi_sum"]["regimen_FDA_S"]:
                    regimen_list_S.append(regimen["regimen_name"])
            if "evi_sum" in var.keys() and var["evi_sum"]["regimen_R"]:
                for n in var["evi_sum"]["regimen_R"]:
                    if n["evi_conclusion_simple"] == "A":
                        regimen_list_R.append(n["regimen_name"])
            
            if regimen_list_S:
                regimen_list_S = "".join([",".join(regimen_list_S), "敏感"])
            if regimen_list_R:
                regimen_list_R = "".join([",".join(regimen_list_R), "耐药"])
            var["regimen_S"] = "".join(regimen_list_S)
            var["regimen_R"] = "".join(regimen_list_R)
        
        return recom_sum
    
    def var_info(level_I, level_II):
        '''
        var['var_for_regimen']
        靶向治疗相关标志物检测结果中，DNA和RNA共检出的变异需要合并在一行展示
        '''
        # 要求不展示胚系的
        var_regimen_for_ZDFY_level_I = [var for var in level_I if var['var_origin'] != 'germline'] if level_I else []
        var_regimen_for_ZDFY_level_II = [var for var in level_II if var['var_origin'] != 'germline'] if level_II else []

        def rna_remove(var_list):
            new_var = var_list
            for var in var_list:
                if var['bio_category'] == 'Sv' and var['rna_detect']:
                    name = var['five_prime_gene'] + var['five_prime_cds'] + var['three_prime_gene'] + var['three_prime_cds']
                    for j in new_var:
                        if j['bio_category'] == 'PSeqRnaSv':
                            j_name = j['five_prime_gene'] + j['five_prime_cds'] + j['three_prime_gene'] + j['three_prime_cds']
                            if name == j_name:
                                new_var.remove(j)
            return new_var
        
        var_regimen_for_ZDFY_level_I = rna_remove(var_regimen_for_ZDFY_level_I)
        var_regimen_for_ZDFY_level_II = rna_remove(var_regimen_for_ZDFY_level_II)

        return var_regimen_for_ZDFY_level_I, var_regimen_for_ZDFY_level_II
    
    def tumor_type(self):
        recom_cancer = ['肺癌', '黑色素瘤', '结直肠癌', '甲状腺癌', '乳腺癌', '胃癌', '胆管癌', '尿路上皮癌', '白血病', '胃肠道间质瘤', '实体瘤', '骨髓增生异常/骨髓增生性疾病', 'Erdheim-Chester病']
        
    
    def run_ZDFY(self):
        report_name = self.MatchReport()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--json_name', dest='json_name', required=True)
    parser.add_argument('-o', '--outfile', dest='outfile', required=True)
    arg = parser.parse_args()
    return arg


if __name__ == '__main__':
    args = parse_args()
    report = ZDFYReport(args.json_name, args.outfile)
    report.run_ZDFY()

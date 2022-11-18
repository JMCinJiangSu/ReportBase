# -*- coding:utf-8 -*-

import argparse
import json
import re
from ReportBase import ReportBase
from VarBase import VarBase, s_var_rule, s_var_rule_gene, g_var_rule, g_var_regimen_rule, var_bptm_rule, var_regimen_rule


class BYReport(ReportBase):
    def __init__(self, json_name, output_div):
        super().__init__(json_name, output_div)
        pass

    # 北京医院检测小结，重新计数
    # I+II+III类+肿瘤发生发展相关变异，融合双检算1个，MET双检算1个
    # 靶向药物相关：体细胞+胚系，只要有药物的都纳入计算

    def BJYY_sum(self, var_data):
        somatic = s_var_rule(var_data)
        germline = g_var_regimen_rule(var_data)
        #DNA+RNA共检出,MET单独处理
        sv_var = [var for var in var_data if (var["bio_category"] == "Sv") and not (var["five_prime_gene"] == "MET" and var["three_prime_gene"] == "MET")]
        Rsv_var = [var for var in var_data if (var["bio_category"] == "PSeqRnaSv") and not (var["five_prime_gene"] == "MET" and var["three_prime_gene"] == "MET")]
        DNA_RNA_met = [var for var in var_data if var["bio_category"] == "Snvindel" and var["gene_symbol"] == "MET" and "judge_mergeMET" in var.keys() and var["judge_mergeMET"]]

        DNA_RNA_var = []
        for i in sv_var:
            for j in Rsv_var:
                if i["var_id"] == j["var_id"]:
                    DNA_RNA_var.append(i)
        
        def var_count(var_list):
            num = 0
            for var in var_list:
                num += 1
                if "rna_detect" in var.keys():
                    num += 1
            return num
        
        drug_num = var_count(somatic['level_I']) + var_count(germline['regimen_level_I']) + var_count(somatic['level_II']) + var_count(germline['regimen_level_II'])
        if DNA_RNA_met and DNA_RNA_var:
            drug_num = drug_num - 1 - len(DNA_RNA_var)
        elif DNA_RNA_var:
            drug_num = drug_num - len(DNA_RNA_var)
        elif DNA_RNA_met:
            drug_num = drug_num - 1
        
        return drug_num
    
    def process_snvindel(self):
        snvindel = self.data_js['snvindel']
        for var in snvindel:
            # 默认格式，hgvs_p加括号，hgvs_p_abbr加括号
            var["hgvs_p_abbr"] = var["hgvs_p_abbr"] if var["hgvs_p_abbr"] else ""
            
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
    
    def getVar_BY(self):
        data = {}
        var_data, var_data_without_rnasv, var_data_rna_sv = self.process_var()
        # 体细胞变异结果整理
        data["var_somatic"] = s_var_rule(var_data)
        data["var_for_regimen"] = var_regimen_rule(var_data)
        # 胚系结果整理
        data["var_germline"] = {**g_var_rule(var_data), **g_var_regimen_rule(var_data)}
        
        data['BJYY_sum'] = self.BJYY_sum(var_data)
        
        var_somatic = data['var_somatic']['level_I'] + data['var_somatic']['level_II'] + data['var_somatic']['level_III'] +data['var_somatic']['level_onco_nodrug']
        data['Sv'] = [var for var in var_somatic if var['bio_category'] == 'Sv']
        data['RnaSv'] = [var for var in var_somatic if var['bio_category'] == 'PSeqRnaSv']
        data['SNV'] = [var for var in var_somatic if var['bio_category'] == 'Snvindel']
        data['CNV'] = [var for var in var_somatic if var['bio_category'] == 'Cnv']

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
        # 免疫正负相关
        data["io"] = {}
        data["io"]["result"], data["io"]["io_p_summary"], data["io"]["io_n_summary"], data['io']['num'] = self.io_detect(var_data)

        # 变异统计
        data['summary'] = {}
        data['summary']['level_I'], data['summary']['level_II'], data['summary']['level_onco_nodrug'], data['summary']['level_III'] = self.Master_sum(var_data)

        return data


    def run_BY(self):
        
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
        self.data['var'] = self.getVar_BY()
        self.data['refer']['fixed'] = self.getfixed_refer(report_name, self.data['sample']['tumor_list'])
        self.data['refer']['dynamic'] =  self.getdynamic_refer(self.data['var'], self.data['hrd'])
        # 输出构建好的用来填充模板的data
        self.dataJson = json.dumps(self.data, ensure_ascii=False)
        with open(self.output_div + '/' + self.json_name + '_to_word.json', 'w', encoding='utf-8') as outFile:
            outFile.write(self.dataJson)

        self.renderreport()

        return


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--json_name', dest='json_name', required=True)
    parser.add_argument('-o', '--outfile', dest='outfile', required=True)
    arg = parser.parse_args()
    return arg


if __name__ == '__main__':
    args = parse_args()
    report = BYReport(args.json_name, args.outfile)
    report.run_BY()

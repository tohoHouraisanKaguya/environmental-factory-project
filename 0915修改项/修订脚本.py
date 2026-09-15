"""Apply the September 15 review to the user-supplied DOCX.

Usage: bundled-python 修订脚本.py INPUT.docx
Original files and previous deliverables are never overwritten.
"""
import sys, re, math, json, hashlib, importlib.util
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
from lxml import etree
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
SOURCE = Path(sys.argv[1])
doc = Document(SOURCE)
original = list(doc.element.body)
changed = []
counts = defaultdict(int)

def para(i): return Paragraph(original[i],doc._body)
def text(i,value):
    p=para(i); p.text=value; changed.append(i); return p
def delete(i):
    e=original[i]
    if e.getparent() is not None: e.getparent().remove(e)
    changed.append(i)
def insert(anchor,value,style='Body Text'):
    p=doc.add_paragraph(value,style)
    anchor.addnext(p._p)
    return p
def lines_after(i,values):
    anchor=original[i]
    for value in values:
        p=insert(anchor,value); anchor=p._p
    return anchor
def table(i,headers,rows):
    old=original[i]; t=doc.add_table(rows=1,cols=len(headers)); t.style='Table Grid'
    for c,v in zip(t.rows[0].cells,headers): c.text=str(v)
    for row in rows:
        for c,v in zip(t.add_row().cells,row): c.text=str(v)
    old.addprevious(t._tbl); old.getparent().remove(old); changed.append(i)
    return t
def formula(i,ch,general,definitions,calculation,source=None):
    p=para(i)
    if source:
        pre=doc.add_paragraph(source,'Body Text'); p._p.addprevious(pre._p)
    counts[ch]+=1
    p.text=general+'    （'+str(ch)+'-'+str(counts[ch])+'）'
    p.style=doc.styles['Normal']; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Pt(0)
    p.paragraph_format.keep_with_next=True
    anchor=p._p
    for j,d in enumerate(definitions):
        a=insert(anchor,('式中：' if j==0 else '　　　')+d)
        a.paragraph_format.first_line_indent=Pt(0)
        a.paragraph_format.left_indent=Cm(.4)
        a.paragraph_format.line_spacing=1.15
        a.paragraph_format.space_after=Pt(0)
        a.paragraph_format.keep_with_next=j<len(definitions)-1
        anchor=a._p
    if calculation:
        a=insert(anchor,'代入计算：'+calculation); anchor=a._p
    changed.append(i)
    return anchor

# Retain cover, course input, water-line geometry and the standards names supplied by the user.
text(13,'供氧采用单位去除BOD₅需氧量法初算，设计需氧量为1403.325 kg O₂/h；空气量采用30000 Nm³/h，配置6000只229 mm盘式微孔曝气器和6台高速离心鼓风机（4用2备）。二沉采用8座净径37 m辐流池；消毒剂采用次氯酸钠，2格接触池总有效容积3456 m³。水力高程自细格栅前EL34.80 m降至计量后EL29.30 m，落差5.50 m；延伸至东厂界EL28.75 m后总落差6.05 m。')
text(86,'本说明书包括水线工艺、构筑物尺寸、回流、供气和水力高程计算。污泥计算止于排泥接口，不包括污泥浓缩、消化、脱水和处置系统。图件表示工艺净尺寸和总平面布置包络。')
text(110,'3.2 水线流程')
text(94,'设计人口N=600000人，人均排水量q=180 L/(人·d)，均由任务书给出。平均日设计水量Q_d和最高时流量Q_max,h计算如下：')
table(107,['具体工艺方案','脱氮除磷及运行特点','本项目比较与选择'],[
 ['常规A²/O（厌氧—缺氧—好氧）','连续进水；厌氧释磷、缺氧反硝化、好氧硝化吸磷；分区及回流可分别控制。','适应10.8万m³/d连续来水；设置4系列便于分组运行。采用本方案。'],
 ['Orbal三沟式氧化沟＋前置厌氧池','同心沟道循环运行，利用不同沟道溶解氧条件脱氮；前置厌氧池用于生物除磷；仍设二沉池。','抗冲击能力较强，但沟道、前置厌氧池和二沉池共同占地；循环曝气与分区控制需统筹。'],
 ['CAST循环式活性污泥工艺（SBR变型）','设置预反应区及主反应区，周期曝气、沉淀与滗水；脱氮除磷依赖周期和分区控制。','可省独立二沉池，但本规模需多池错峰及滗水设备，连续来水与周期出水的衔接较复杂。']])
lines_after(108,['比较依据：任务书给出的平均日水量108000 m³/d、厂区面积12 hm²和脱氮除磷目标，以及参考图集第三章氧化沟、SBR及其变形工艺的构造和运行特点。未以缺少尺寸计算的占地数值或缺少报价的经济数值作比选结论。'])
text(109,'综合连续来水、脱氮除磷要求、运行分组和已有平面布置，本设计采用常规A²/O。初沉池去除部分悬浮物和有机物；A²/O分别设置厌氧、缺氧和好氧区。缺氧区设置甲醇加药接口，A²/O出水至二沉池前设置三氯化铁辅助除磷接口。')
table(116,['参数及中文含义','设计值','来源或属性'],[
 ['Kz——总变化系数','1.50（无量纲）','GB 50014—2021流量变化系数；沿用课程设计值'],
 ['设计温度','15 ℃','任务书冬季平均温度；不等同于最低连续水温'],
 ['MLSS——混合液悬浮固体浓度','3.50 kg/m³','HJ 576—2010表5设计浓度范围'],
 ['MLVSS——混合液挥发性悬浮固体浓度','2.45 kg/m³','MLVSS=0.70×MLSS'],
 ['y——挥发性固体所占质量比例','0.70（无量纲）','HJ 576—2010表5，设初沉池的比例范围'],
 ['SRT——污泥停留时间（泥龄）','20 d','HJ 576—2010表5设计范围'],
 ['R——回流污泥流量比','0.75（无量纲）','Q_R=RQ；设计取值'],
 ['R_i——混合液内回流流量比','2.50（无量纲）','Q_IR=R_iQ；设计取值'],
 ['HRT——水力停留时间','14.0 h','63000 m³÷4500 m³/h；分区见表8-1'],
 ['设计出水浓度','BOD₅/SS/TN/NH₄⁺-N/TP=20/20/20/8/1 mg/L','课程任务书']])
lines_after(117,['Q表示污水设计流量，使用回流公式时，各流量必须采用同一工况和同一单位。0.75Q、2.50Q分别表示回流污泥流量和混合液内回流流量，具有流量单位；0.75、2.50为流量比，无量纲。RAS为回流污泥系统缩写，IR为混合液内回流系统缩写。','单位约定：m为米，mm为毫米，m²为平方米，m³为立方米；s、min、h、d分别为秒、分钟、小时、日；kg为千克，mg为毫克，L为升，kPa为千帕，kW为千瓦，℃为摄氏度。DN表示公称直径，其数值以毫米表示；EL表示标高，单位m。Nm³在本说明书中指0 ℃、101325 Pa下的空气体积，区别于HJ 576—2010定义的20 ℃标准状态。','水质缩写：BOD₅——五日生化需氧量；COD——化学需氧量；SS——悬浮物；TN——总氮；TP——总磷；NH₄⁺-N——氨氮；TKN——总凯氏氮；NOx-N——硝态氮与亚硝态氮之和；DO——溶解氧。浓度单位均为mg/L。'])
# Remove an input row that had no data; preserve the discharge target in table 3-2.
table(102,['指标','进水负荷 kg/d','进水浓度 mg/L','出水目标 mg/L','最低去除率'],[
 ['BOD₅','18000','166.67','20','88.0%'],['SS','30000','277.78','20','92.8%'],['TN','4800','44.44','20','55.0%'],['TP','600','5.56','1.0','82.0%']])
lines_after(103,['各进水浓度按任务书日负荷除以平均日水量换算：C=1000M/Q_d；式中，C——进水浓度，mg/L；M——污染物日负荷，kg/d；Q_d——平均日设计水量，m³/d。最低去除率按η=(C_in−C_out)/C_in×100%计算；C_in、C_out分别为进、出水浓度，mg/L；η为去除率。氨氮出水目标见表3-2，不采用TN替代未给出的进水氨氮。'])

formula(95,2,'Q_d=Nq/1000',['Q_d——平均日设计水量，m³/d；','N——设计服务人口，人；','q——人均日排水量，L/(人·d)；1000为L与m³换算系数。'],'600000×180/1000=108000 m³/d；Q_h=Q_d/24=4500 m³/h；Q_s=Q_d/86400=1.250 m³/s。')
formula(96,2,'Q_max,h=KzQ_h',['Q_max,h——最高时设计流量，m³/h；','Kz——总变化系数，无量纲；','Q_h——平均日水量折算的小时流量，m³/h。'],'1.50×4500=6750 m³/h=1.875 m³/s。')
formula(122,4,'v=Q√(sinα)/(bnh)',['v——过栅流速，m/s；','Q——单台格栅最高时流量，m³/s；','b——栅条净间隙，m；','n——净空隙数量，个；','h——栅前正常水深，m；','α——格栅与水平面的夹角，°。'],'粗格栅：0.9375√(sin60°)/(0.025×48×0.80)=0.909 m/s；细格栅：0.9375√(sin60°)/(0.010×122×0.80)=0.894 m/s。','两条水线平均分担6750 m³/h最高时流量，单台Q=0.9375 m³/s；沿用α=60°、h=0.80 m，栅隙分别为25 mm及10 mm，计算时换算为m。')
lines_after(128,['堵塞校核采用h_b=Q√(sinα)/[bn(1−p)v_lim]；式中，h_b——堵塞后的所需水深，m；p——堵塞比例，取0.25，无量纲；v_lim——允许过栅流速，取1.0 m/s；其余符号同式（4-1）。粗、细格栅分别计算得0.969 m、0.953 m。栅条组合宽度按B=bn+s(n−1)计算；B——组合宽度，m；s——栅条厚度，m，粗、细分别为0.010 m、0.007 m；计算得1.670 m、2.067 m。','清洁水头损失采用h_0=ξv²sinα/(2g)，ξ=β_g(s/b)^(4/3)；式中，h_0——清洁水头损失，m；ξ——阻力系数，无量纲；β_g——矩形栅条形状系数，取2.42，无量纲；g——重力加速度，9.81 m/s²。按表4-1的流速计算，粗、细格栅分别为0.019 m、0.039 m；设计损失按2h_0计，分别为0.038 m、0.078 m。'])
text(130,'粗格栅栅隙为25 mm，按《给水排水设计手册》第5册第280页中16～25 mm栅隙的湿栅渣量范围，采用每1000 m³污水产生0.05 m³湿栅渣。两级格栅均设置密闭输送和压榨接口。')
formula(130,4,'W_c=Q_dw_c/1000',['W_c——粗格栅湿栅渣量，m³/d；','Q_d——全厂平均日污水量，108000 m³/d；','w_c——每1000 m³污水对应的湿栅渣体积，0.05 m³。'],'108000×0.05/1000=5.40 m³/d。','粗格栅湿栅渣产率采用《给水排水设计手册》第5册第280页对应25 mm栅隙的0.05 m³/1000 m³污水。细格栅增量、两级合计和湿栅渣质量不以缺少依据的相同产率或密度计算。')
text(133,'进水井设两格，每格净平面16 m×10 m、调节水深1.20 m，有效调节容积192 m³。每格设3个泵位，按2用1备运行；全厂6台同型潜污泵，最高时4台工作，两条水线各2台工作。调节段上下控制水位分别为EL23.80 m和EL22.60 m。')
formula(134,5,'V_min=Q_pt_p；h_min=V_min/(LB)',['V_min——按单泵运行时长计算的最小调节容积，m³；','Q_p——单泵额定流量，0.46875 m³/s；','t_p——控制运行时长，5 min=300 s；','L、B——每格调节水面净长、净宽，分别为16 m、10 m；','h_min——对应平面面积的最小调节水深，m。'],'V_min=0.46875×300=140.625 m³；h_min=140.625/(16×10)=0.879 m。设计水深h=23.80−22.60=1.20 m，大于0.879 m。','单泵流量由全厂最高时6750 m³/h÷4台工作泵确定。沿用GB 50014—2021泵站调节容积的单泵5 min出水量校核口径；平面尺寸和上下启停水位来自本设计泵站布置。')
formula(135,5,'V_cell=LBh',['V_cell——每格有效调节容积，m³；','L、B——调节段平面净尺寸，m；','h——上下控制水位之间的调节水深，m。'],'16×10×1.20=192 m³>140.625 m³；对应单泵出水时间192/0.46875/60=6.83 min。')
formula(141,5,'H_req=Δz+h_branch+h_main+h_add',['H_req——提升泵所需扬程，m；','Δz——细格栅前水位与进水井最低水位之差，m；','h_branch、h_main——支管、出水管水头损失，m；','h_add——阀件和设备接口附加水头，设计采用0.80 m。'],'(34.80−22.60)+0.371057+0.306825+0.80=13.677882 m；采用H=14 m。')
formula(142,5,'P_shaft=ρgQ_pH/(1000η_p)',['P_shaft——泵轴功率，kW；','ρ——水密度，1000 kg/m³；','g——重力加速度，9.81 m/s²；','Q_p——单泵设计流量，m³/s；','H——采用扬程，m；','η_p——设计泵效率，0.80，无量纲；1000为W与kW换算系数。'],'1000×9.81×0.46875×14/(1000×0.80)=80.47 kW；乘1.10设计余量得88.52 kW，选90 kW电机。')
text(143,'所需扬程13.677882 m，采用14 m；电机额定轴输出功率采用90 kW。电输入功率P_in=P_shaft/η_m；式中，P_in——电输入功率，kW；η_m——电机效率，无量纲。')
formula(150,6,'v_H=Q/(Bh)',['v_H——池内水平流速，m/s；','Q——单池最高时流量，m³/s；','B——单池净宽，m；','h——有效水深，m。'],'0.9375/(3.80×2.55)=0.0967 m/s。','单池流量取最高时全厂流量的一半；B=3.80 m、h=2.55 m来自单池设计净尺寸。')
formula(151,6,'t=V/(60Q)；V=LBh',['t——水力停留时间，min；','V——单池有效容积，m³；','Q——相应工况的单池流量，m³/s；','L、B、h——净长、净宽、有效水深，m；60为s与min换算系数。'],'V=30×3.80×2.55=290.70 m³；最高时t=290.70/(60×0.9375)=5.168 min；平均日t=290.70/(60×0.625)=7.752 min。')
text(158,'曝气沉砂池线供气强度采用6 L/(m·s)，位于GB 50014—2021第7.4节规定的5～12 L/(m·s)范围内。单池沿30 m池长布气。单池供气量G_a=I_aL=6×30=180 L/s=648 m³/h；两池合计1296 m³/h。式中，G_a——单池供气量；I_a——单位池长供气强度，L/(m·s)；L——池长，m。该供气量单独计入沉砂池供气系统，不混入生物池的30000 Nm³/h。池底为平底，水位EL34.25 m、池底EL31.70 m；吸砂机往复排砂至池外砂水分离器。')
text(159,'产砂率采用GB 50014—2021沉砂池设计的0.03 L/m³，即每1000 m³污水产生0.03 m³砂。平均日全厂产砂量V_s=Q_da_s/1000=108000×0.03/1000=3.24 m³/d，平均每池1.62 m³/d。式中，V_s——全厂日砂量，m³/d；Q_d——平均日污水量，m³/d；a_s——单位污水产砂率，L/m³。单池两日产砂量为1.62×2=3.24 m³；池外储砂斗有效容积3.20 m³，对应3.20/1.62=1.98 d，按每日排砂运行。')
formula(163,7,'q_s=Q_max,h/(n_cLB)',['q_s——最高时表面水力负荷，m³/(m²·h)；','Q_max,h——全厂最高时流量，m³/h；','n_c——初沉池座数，4；','L、B——单池净长、净宽，m。'],'6750/(4×58×14.5)=2.006 m³/(m²·h)。')
formula(164,7,'t=LBh/(Q_max,h/n_c)',['t——最高时停留时间，h；','h——有效水深，3.50 m；','其余符号同式（7-1）。'],'58×14.5×3.5/(6750/4)=1.744 h。')
formula(165,7,'v_H=Q_c/(Bh)',['v_H——水平流速，m/s；','Q_c——单池最高时流量，0.46875 m³/s；','B、h——单池净宽、有效水深，m。'],'0.46875/(14.5×3.5)=0.00924 m/s。')
lines_after(173,['出水堰负荷采用q_w=1000Q_c/L_w；式中，q_w——堰负荷，L/(m·s)；Q_c——单池最高时流量，m³/s；L_w——有效总堰长，m。代入得1000×0.46875/(12×14)=2.790 L/(m·s)。泥斗容积采用V_h=L_h(B_t+B_b)h_h/2；式中，V_h——梯形条形泥斗容积，m³；L_h——沿池宽的泥斗长度14.5 m；B_t、B_b——泥斗上、下口纵向宽度3.0 m、0.8 m；h_h——泥斗深度2.0 m；计算得55.10 m³。'])
delete(178)  # Redundant nitrogen explanation otherwise creates an almost empty page.
lines_after(184,['各区容积按V_j=Q_ht_j计算；式中，V_j——全厂相应分区有效容积，m³；Q_h——全厂平均日小时流量4500 m³/h；t_j——相应分区水力停留时间，h。代入1.50、4.80、7.70 h，分别得6750、21600、34650 m³；总计63000 m³。单系列容积为V_j/4，等效长度为(V_j/4)/(7.5×5)，其中7.5 m为廊道净宽、5 m为净水深。分区HRT为现有布置设计值，本节不将其作为缺少TKN资料时的反硝化动力学验证结果。'])
formula(189,8,'L_MLSS=M_BOD/(VX)',['L_MLSS——以MLSS计的BOD₅污泥负荷，kg BOD₅/(kg MLSS·d)；','M_BOD——初沉后进水BOD₅日负荷，13500 kg/d；','V——生物池总有效容积，63000 m³；','X——MLSS浓度，3.50 kg/m³。'],'13500/(63000×3.50)=0.0612 kg BOD₅/(kg MLSS·d)。')
formula(190,8,'L_MLVSS=M_BOD/(VX_v)',['L_MLVSS——以MLVSS计的BOD₅污泥负荷，kg BOD₅/(kg MLVSS·d)；','X_v——MLVSS浓度，X_v=yX=0.70×3.50=2.45 kg/m³；','y——MLVSS占MLSS的质量比例，无量纲；M_BOD、V同式（8-1）。'],'13500/(63000×2.45)=0.0875 kg BOD₅/(kg MLVSS·d)。')
text(191,'MLSS、MLVSS质量比例、SRT和回流比采用HJ 576—2010表5的设计范围；分区容积见表8-1。厌氧区DO小于0.2 mg/L，缺氧区0.2～0.5 mg/L，好氧区不低于2 mg/L。')
table(194,['系统及流量公式','全厂平均 m³/h','全厂最高时 m³/h','最高时单系列 m³/h'],[['回流污泥：Q_R=RQ，R=0.75','3375','5062.5','1265.625'],['内回流：Q_IR=R_iQ，R_i=2.50','11250','16875','4218.75']])
lines_after(195,['式中：Q_R——回流污泥流量，m³/h；Q_IR——混合液内回流流量，m³/h；Q——相应工况污水流量，m³/h；R、R_i——回流比，无量纲。平均工况Q=4500 m³/h，最高时Q=6750 m³/h；最高时单系列流量为全厂回流流量除以4。'])

# Delete all quantitative conclusions dependent on unprovided nitrogen, carbon and alkalinity inputs.
text(200,'9 脱氮与辅助加药接口')
text(201,'9.1 缺氧区容积')
text(202,'缺氧区有效容积采用表8-1的21600 m³，按平均日水量折算水力停留时间。')
formula(203,9,'t_n=V_n/Q_h',['t_n——缺氧区水力停留时间，h；','V_n——全厂缺氧区有效容积，21600 m³；','Q_h——全厂平均日小时流量，4500 m³/h。'],'21600/4500=4.80 h。')
for i in [204,205,206,209,213,219]: delete(i)
text(207,'9.2 外加碳源接口')
text(208,'缺氧区设置甲醇投加接口，以硝态氮、总氮和有机碳监测控制投加。碳源需求取决于可利用有机碳和实际反硝化氮量。')
text(210,'甲醇计量设施按工作与备用两套接口布置；本说明书不列缺少碳源数据时的定量药耗与泵流量。')
text(211,'9.3 辅助除磷接口')
text(212,'辅助除磷药剂采用三氯化铁，投加点设置在A²/O出水后、二沉池前。药耗计算需使用生物处理后实测TP和混凝试验结果。')
text(214,'设置三氯化铁工作、备用计量接口。化学药耗与新增固体量不采用缺少试验依据的生物除磷率和铁磷比计算。')
text(216,'图9-1 辅助加药与排泥接口图')
text(217,'9.4 生物固体库存与排固')
text(218,'生物固体库存由总有效容积和设计MLSS计算，排固量按20 d泥龄折算。此处计算不含未确定的化学新增固体。')
table(221,['项目','计算式','结果'],[['生物固体库存','M_X=VX=63000×3.50','220500 kg'],['20 d泥龄对应排固量','M_w=M_X/SRT=220500/20','11025 kg/d']])
solids_end=lines_after(222,['式中：M_X——生物池悬浮固体库存，kg；V——总有效容积，m³；X——设计MLSS，kg/m³；M_w——按泥龄折算的生物固体排出量，kg/d；SRT——污泥停留时间，d。排固量不是湿污泥体积，未给出含固率时不换算为m³/d。'])
solids_end.addnext(original[215]);original[215].addnext(original[216])

transfer=.80*(.95*9.29844016842796-2)*1.024**5/9.17
o_daily=1.8*11340; aor=o_daily/24*1.5*1.10; sor=aor/transfer
gs=sor/(.28*.25); gn=gs*273.15/293.15
capacity=30000*293.15/273.15*.28*.25*transfer
slr=162000*1.75*3.5/(8*math.pi*(37**2-6**2)/4)
text(225,'初沉后BOD₅浓度为125 mg/L，目标为20 mg/L，平均日水量108000 m³/d。采用HJ 576—2010表5的单位BOD₅需氧量设计范围1.1～1.8 kg/kg，取1.8 kg O₂/kg BOD₅作供氧初算；最高时系数采用1.50，设备余量系数采用1.10。本节为负荷法初算，不以TN替代TKN完成式(15)物料衡算。')
formula(226,10,'M_rem=Q_d(S_0−S_e)/1000；O_d=k_OM_rem',['M_rem——每日去除BOD₅质量，kg/d；','Q_d——平均日水量，m³/d；','S_0、S_e——生物池进、出水BOD₅浓度，mg/L；','O_d——负荷法初算日需氧量，kg O₂/d；','k_O——单位去除BOD₅需氧量，1.8 kg O₂/kg BOD₅。'],'M_rem=108000×(125−20)/1000=11340 kg/d；O_d=1.8×11340=20412 kg O₂/d。')
table(228,['计算项目','采用值或结果'],[['每日去除BOD₅','11340 kg/d'],['单位BOD₅需氧量','1.8 kg O₂/kg BOD₅'],['平均日需氧量','20412 kg O₂/d'],['最高时系数／设备余量系数','1.50／1.10（均无量纲）']])
formula(230,10,'AOR_design=(O_d/24)KzK_m',['AOR_design——设计工况实际需氧量初算值，kg O₂/h；','O_d——初算日需氧量，kg O₂/d；','Kz——最高时流量系数，1.50；','K_m——设备余量系数，1.10；24为d与h换算系数。'],'(20412/24)×1.50×1.10=1403.325 kg O₂/h。')
text(232,'供氧换算按HJ 576—2010式(16)～(20)的状态修正方法。设计采用α=0.80、β=0.95、T=25 ℃、DO=2 mg/L、曝气器淹没4.75 m；沿用原稿中间深度饱和溶解氧C_sm=9.29844 mg/L和20 ℃清水饱和溶解氧C_20=9.17 mg/L。空气氧质量密度采用0.28 kg O₂/m³（20 ℃），设计氧利用率E_A=0.25。以上为供气初算设计参数，不是实测转移效率。')
formula(233,10,'f=α(βC_sm−C_L)1.024^(T−20)/C_20；SOR=AOR_design/f',['f——污水工况相对于20 ℃标准供氧的转移修正系数，无量纲；','α、β——污水传质及饱和溶解氧修正系数，无量纲；','C_sm、C_L、C_20——中间深度饱和溶解氧、池内DO及20 ℃清水饱和溶解氧，mg/L；','T——设计曝气水温，℃；','SOR——20 ℃标准状态需氧量，kg O₂/h；AOR_design同式（10-2）。'],f'f={transfer:.6f}；SOR=1403.325/{transfer:.6f}={sor:.3f} kg O₂/h。')
formula(234,10,'G_20=SOR/(ρ_OE_A)；G_N=G_20T_N/T_20',['G_20——20 ℃、101325 Pa下空气流量，m³/h；','ρ_O——该状态空气中的氧质量密度，0.28 kg O₂/m³；','E_A——设计氧利用率，0.25，无量纲；','G_N——0 ℃、101325 Pa下空气流量，Nm³/h；','T_N、T_20——0 ℃、20 ℃的绝对温度，273.15 K、293.15 K。'],f'G_20={sor:.3f}/(0.28×0.25)={gs:.3f} m³/h；G_N={gs:.3f}×273.15/293.15={gn:.3f} Nm³/h；采用30000 Nm³/h。')
formula(235,10,'n_d=G_adopt/g_d；n_series=n_d/4',['n_d——全厂生物池曝气器数量，只；','G_adopt——采用空气流量，30000 Nm³/h；','g_d——单只曝气器设计风量，5.0 Nm³/h；','n_series——单系列曝气器数量，只。'],f'n_d=30000/5=6000只；每系列1500只。好氧区底面积为34650/5=6930 m²，密度6000/6930=0.866只/m²。按设计转移参数，供氧能力{capacity:.3f} kg O₂/h，比初算需氧量高{(capacity/aor-1)*100:.2f}%。','曝气器采用原稿229 mm盘式微孔曝气器类型，单只5.0 Nm³/h为布气设计点。以重新计算的生物池供气量确定数量。')
text(242,'设6台高速离心鼓风机，4用2备；单台设计风量7500 Nm³/h、出口表压65 kPa，4台工作总风量30000 Nm³/h。数量计算为30000/7500=4台工作，另设2台备用。空气母管DN1200、4根系列支管DN700；管径、走向及压力预算沿用原设计，风量降低后不引用原48000 Nm³/h下的2.523 kPa计算值作为新工况结果。')
lines_after(241,['压力按p_req=ρgH_s/1000+Δp_d+Δp_pipe+Δp_m计算；式中，p_req——所需表压，kPa；ρ——水密度1000 kg/m³；g——9.81 m/s²；H_s——淹没深度4.75 m；Δp_d——曝气器设计阻力5 kPa；Δp_pipe——管阀设计压力预算6 kPa；Δp_m——设计余量3 kPa。代入得46.60+5+6+3=60.60 kPa，选65 kPa。表压指相对于大气压的压力，原稿中的(g)表示表压，不是另一个单位。'])
table(240,['压力项','压力 kPa'],[['4.75 m淹没静压','46.60'],['曝气器设计阻力','5.00'],['管网与阀件预算','6.00'],['设计余量','3.00'],['合计','60.60'],['采用表压','65.00']])
formula(246,11,'A_net=n_sπ(D_s²−D_c²)/4',['A_net——全部二沉池有效沉淀面积，m²；','n_s——二沉池座数，8；','D_s——池内净径，37 m；','D_c——中心进水井直径，6 m。'],'8×π×(37²−6²)/4=8375.486 m²。')
table(248,['校核项','计算值','设计控制值或结论'],[['最高时表面负荷','0.806 m³/(m²·h)','按外部最高时流量计算'],['最高时外部HRT','3.847 h','1.5～4 h'],['池径／沉淀水深','11.94（无量纲）','6～12'],['最高时生物固体负荷',f'{slr:.3f} kg/(m²·d)','小于150；不含未定化学固体'],['最高时堰负荷','1.130 L/(m·s)','小于1.7']])
text(253,'二沉生物固体负荷按设计MLSS=3.50 kg/m³计算，混合液流量包括外部污水与回流污泥。未确定的化学新增固体不计入本项生物固体负荷。')
formula(254,11,'SLR_max=Q_eq(1+R)X/A_net',['SLR_max——最高时工况折算的生物固体负荷，kg/(m²·d)；','Q_eq——最高时污水流量折算的等效日流量，6750×24=162000 m³/d；','R——污泥回流比，0.75，无量纲；','X——设计MLSS，3.50 kg/m³；','A_net——二沉池有效沉淀总面积，m²。'],f'162000×(1+0.75)×3.50/8375.486={slr:.3f} kg/(m²·d)，小于150。')
text(257,'每池进水混合液支管DN900，最高时Q_in=6750×(1+0.75)/8/3600=0.410156 m³/s；出水支管DN700，Q_out=6750/8/3600=0.234375 m³/s。双侧环形堰中心线直径D_w=33 m，与37 m池净径不同；堰中心线距池内壁(37−33)/2=2.0 m。双侧有效堰长L_w=2πD_w=207.35 m，堰负荷q_w=1000Q_out/L_w=1.130 L/(m·s)。式中，Q_in、Q_out——单池进、出水流量，m³/s；D_w——环形槽堰中心线直径，m；L_w——双侧总堰长，m；q_w——堰负荷，L/(m·s)。两侧堰线等效直径之和为66 m，不能把33 m写成池径。主体水位EL31.15 m，周边工艺底EL27.15 m，坡底内缘EL26.375 m，坑底EL25.875 m。')
lines_after(249,['水力校核：q_s=6750/8375.486=0.806 m³/(m²·h)；t=8375.486×3.1/6750=3.847 h；D_s/h_s=37/3.1=11.94。式中，q_s——表面水力负荷；t——按外部污水流量计算的HRT，h；h_s——沉淀区有效水深，m。中心井内半径3 m，池内半径18.5 m，径向坡长15.5 m；坡降Δh=i(18.5−3)=0.05×15.5=0.775 m。i为池底坡度，无量纲；Δh为坡降，m。贮泥层容积为(A_net/8)×0.40=418.77 m³；环形坡底楔体容积为308.20 m³；中心泥坑π×6²×0.50/4=14.14 m³，总计741.11 m³/池。'])
formula(261,12,'A=πD²/4；v=Q/A；h_f=λ(L/D)v²/(2g)；h_l=Σζv²/(2g)',['A——满管过水面积，m²；','D——管内径，m；','v——管内平均流速，m/s；','Q——相应管段设计流量，m³/s；','h_f、h_l——沿程、局部水头损失，m；','λ——沿程阻力系数，无量纲；','L——管段中心线长度，m；','Σζ——局部阻力系数之和，无量纲；','g——重力加速度，9.81 m/s²。'],'各管段的Q、DN及L见表12-1，采用实际内径计算；不同管段分别求损失后相加。')
formula(263,12,'h_f=L[n_Mv/R_h^(2/3)]²',['h_f——明渠沿程水头损失，m；','L——渠段长度，m；','n_M——Manning糙率，设计采用0.013 s/m^(1/3)；','v——断面平均流速，m/s；','R_h——水力半径，R_h=A/P_w，m；','A——过水面积，m²；P_w——湿周，m。'],'按各渠段实际断面求A、P_w及R_h，再计算h_f。')
text(260,'压力主水线采用λ=0.025；λ=0.030仅用于参数敏感性校核。局部阻力按各构造的Σζ计算。管线长度取总平面坐标折线的中心线长度，另计竖管和设备连接。')
text(262,'明渠沿程损失采用Manning公式：')
formula(277,12,'h_w=[Q/(1.84b_w)]^(2/3)',['h_w——矩形薄壁堰堰上水头，m；','Q——每条二沉配水支路最高时流量，m³/s；','b_w——单堰净宽，1.20 m；','1.84——所用矩形薄壁堰流量公式系数，单位m^(1/2)/s。'],'[0.410156/(1.84×1.20)]^(2/3)=0.3256 m；采用堰上水头预算0.35 m。')

# Reconstruct occupancy and road areas from the exact existing layout coordinates.
spec=importlib.util.spec_from_file_location('layout',ROOT/'scripts/check_second_revision_batch5_layout.py')
layout=importlib.util.module_from_spec(spec); spec.loader.exec_module(layout)
area_rows=[]
for u in layout.UNITS:
    category={'water':'水处理','auxiliary':'辅助','management':'管理','future':'发展'}[u['category']]
    area_rows.append([u['code']+' '+u['name'],f"({u['cx']:g}, {u['cy']:g})",f"{u['width']:g}×{u['height']:g}",f"{u['width']*u['height']:g}",category])
area_t=doc.add_table(rows=1,cols=5); area_t.style='Table Grid'
for c,v in zip(area_t.rows[0].cells,['图中编号及单元','中心坐标 m','包络长×宽 m','面积 m²','类别']):c.text=v
for row in area_rows:
    for c,v in zip(area_t.add_row().cells,row):c.text=v
original[290].addnext(area_t._tbl)
caption=doc.add_paragraph('表13-3 总平面包络面积逐项计算');area_t._tbl.addprevious(caption._p)
text(288,'厂区采用400 m×300 m矩形，面积400×300=120000 m²=12 hm²。设置6 m厂界环路和三条6 m横向联系路，南侧设4 m次通道。管理区靠南侧主门布置，与工艺和辅助设施分隔；发展用地位于西北侧。表13-3所列包络尺寸及中心坐标对应图13-1方框，包络包括平面布置所需的操作空间，不作为构筑物工艺净尺寸。')
lines_after(291,['面积计算：各矩形包络采用A_i=L_iB_i；式中，A_i——第i个单元的占地包络面积，m²；L_i、B_i——该单元图示包络长、宽，m。水处理面积为全部“水处理”类别面积之和：192+576+392+2×272+2×100+2×216+1150+352+4×1260+4×3750+8×1764=37990 m²。辅助与管理面积为864+756+1672+968+748=5008 m²；发展面积为140×20=2800 m²。','道路矩形按图13-1坐标设置：西、东侧环路各6×288 m；北、南侧环路各376×6 m；三条横向联系路各376×6 m；南侧次通道376×4 m。东西侧路的x范围分别为6～12 m、388～394 m，其余路x范围为12～388 m，各段仅边缘连接，没有重复面积。A_road=2×6×288+5×376×6+376×4=16240 m²。式中，A_road——道路并集面积，m²。','已分配占地A_used=37990+5008+2800+16240=62038 m²；其余用地A_other=120000−62038=57962 m²。式中，A_used、A_other分别为已分配及其余用地面积，m²。表13-2合计120000 m²。绿化未绘出边界，不另列未经图面面积计算的36000 m²绿化结论。'])
text(292,'表13-2列示图面占地包络的面积平衡。构筑物净尺寸见表13-1，包络尺寸见表13-3，两者分别用于工艺水力计算和总平面面积统计。')
para(312).add_run(' 厂内DN1500出厂管48 m已计入水线，控制井EL28.75 m；厂外管线及尾水资料未给，不作厂外水力计算。')
delete(313)
formula(317,15,'V_req=Q_max,ht_c/60；t_max=60V_total/Q_max,h',['V_req——最高时工况所需接触容积，m³；','Q_max,h——全厂最高时流量，6750 m³/h；','t_c——设计接触时间，30 min；','V_total——两格总有效容积，3456 m³；','t_max——实际最高时接触时间，min。'],'V_req=6750×30/60=3375 m³；t_max=60×3456/6750=30.72 min。')
text(318,'两格正常同时运行；单格检修时需限流。每格净水宽8.0 m为4条2.0 m廊道的宽度之和，不包括隔墙，图中的总平面包络50 m×23 m包括布置和操作空间。')
text(322,'消毒剂统一采用次氯酸钠溶液；有效氯是药剂氧化能力的计量指标，不是另选一种消毒剂。按GB 50014—2021接触消毒的设计投加量范围，采用有效氯剂量5 mg/L。供货设计指标采用有效氯质量浓度100 g/L（即100 kg/m³），直接据此计算商品液体积，不将“10%次氯酸钠质量分数”当成“10%有效氯”。')
table(324,['工况','次氯酸钠剂量（以有效氯计）','有效氯质量流量','商品溶液流量（100 g/L有效氯）'],[['平均日','5 mg/L','540 kg/d','5.40 m³/d'],['最高时','5 mg/L','33.75 kg/h','0.3375 m³/h']])
lines_after(325,['药剂量计算：M_Cl=Q_dD_Cl/1000；V_sol=M_Cl/c_Cl。式中，M_Cl——有效氯日质量，kg/d；Q_d——平均日污水量，m³/d；D_Cl——次氯酸钠投加剂量，以有效氯计，mg/L；V_sol——次氯酸钠商品液体积，m³/d；c_Cl——商品液有效氯质量浓度，100 kg/m³。代入得108000×5/1000=540 kg/d，540/100=5.40 m³/d。最高时将Q_d换为Q_max,h=6750 m³/h，得33.75 kg/h及0.3375 m³/h。'])
text(326,'设置2台隔膜计量泵，1用1备，单台设计流量0.40 m³/h，大于最高时0.3375 m³/h。储存工作容积按7 d设计库存计算：V_store=7×5.40=37.80 m³；采用2座各20 m³工作容积储罐，合计40 m³。式中，V_store——次氯酸钠储存工作容积，m³；7——设计储存天数，d。加药采用污水流量前馈与余氯反馈控制。')
formula(329,15,'y_c=[Q²/(gb²)]^(1/3)',['y_c——矩形喉道临界水深，m；','Q——单条计量渠最高时流量，0.9375 m³/s；','g——重力加速度，9.81 m/s²；','b——喉道净宽，1.50 m。'],'[0.9375²/(9.81×1.50²)]^(1/3)=0.341479 m。')
text(330,'计量上游水位EL30.05 m，喉底EL29.527691 m，临界水面EL29.869170 m；计量后水位EL29.30 m。临界能量按E_c=1.5y_c=0.512219 m计算；式中，E_c——临界比能，m；y_c——临界水深，m。喉底按EL30.05−E_c−0.01009=EL29.527691 m设置，其中0.01009 m为原设计采用的喉前损失。')
text(341,'本次核对了设计流量、主要水线尺寸、回流、供气初算、二沉生物固体负荷、接触消毒和总平面面积。公式按数据来源、通用公式、符号释义和代入结果编排，正文与相关图表采用一致的设计值。')
text(342,'封面班级、组号及成员信息由提交人填写。脱氮动力学和辅助药剂定量需要TKN、氨氮、可利用碳源、碱度及投药试验资料；供氧负荷法初算不替代完整氮物料衡算，二沉生物固体负荷不含未确定的化学新增固体。')
lines_after(355,['[13] 李杰主编，华海杰、马东华副主编. 城镇污水处理设计入门及参考图集. 北京：化学工业出版社，2021.'])

# Update summary tables without changing other original cells.
for i in [334,338]:
    t=Table(original[i],doc._body)
    for row in t.rows:
        label=row.cells[0].text
        if '辐流二沉池' in label:
            row.cells[-1].text=f'生物SLR_max={slr:.3f} kg/(m²·d)'
        if '微孔曝气器' in label:
            row.cells[1].text='6000只'; row.cells[-1].text='每系列1500只'
        if '高速离心鼓风机' in label: row.cells[2].text='7500 Nm³/h，出口表压65 kPa'
        if '甲醇计量泵' in label or 'FeCl' in label:
            row.cells[2].text='工作、备用加药接口';row.cells[-1].text='按监测及投药试验确定流量'
        if 'NaOCl计量泵' in label:
            row.cells[0].text='次氯酸钠计量泵';row.cells[2].text='0.40 m³/h/台';row.cells[-1].text='流量、余氯反馈'
    changed.append(i)

# Produce editable monochrome figures using existing coordinates and geometry.
svg_src=ROOT/'第二次修改协作项目_2026-09-13/02_成果回收/第09组_位图整图重绘/可编辑SVG'
svg_out=OUT/'图件'; svg_out.mkdir(exist_ok=True)
replacements={
 '设备容量6.5 t/d':'甲醇加药接口','设备容量2.0 m³/d':'三氯化铁加药接口',
 '80%甲醇':'甲醇','40% FeCl₃':'三氯化铁',
 'IR=2.50Q':'Q_IR=2.50Q','RAS=0.75Q':'Q_R=0.75Q',
 '采用48000':'采用30000','48000 Nm³/h':'30000 Nm³/h','12000 Nm³/h':'7500 Nm³/h',
 '2400盘×5 Nm³/h':'1500只×5 Nm³/h','9600盘':'6000只',
 '名义5 mg/L；设备15 mg/L':'以有效氯计：5 mg/L',
 '计量泵2台（1用1备）×1.0 m³/h':'计量泵2台（1用1备）×0.40 m³/h',
 '总MLSS 3.738650 kg/m³':'生物MLSS 3.50 kg/m³',
 '峰值SLR 126.683 kg/(m²·d)':f'生物SLR {slr:.3f} kg/(m²·d)',
 '峰值SLR=126.683 kg/(m²·d)':f'生物SLR={slr:.3f} kg/(m²·d)',
 '总排固11776.747 kg/d':'生物排固11025 kg/d',
 '化学库存15034.947 kg':'不含未定化学固体',
 '化学干固体751.747 kg/d':'三氯化铁投加接口',
 '15 mg/L设备容量→接触池':'唯一消毒剂→接触池',
 '药剂按设备容量表达；生物固体库存、化学固体和排泥量采用第03/04组冻结口径':'辅助加药接口与生物固体计算；未确定药耗及化学固体不列数值',
 '图9-1  投药与固体闭合边界图':'图9-1  辅助加药与排泥接口图',
 '外加COD容量单列':'碳源投加接口',
 'VSS/ISS实测后再细分':'生物固体排出接口',
 '需气量40638 Nm³/h；采用48000；9600盘；供氧余量18.12%':f'初算需气量{gn:.0f} Nm³/h；采用30000；6000只曝气器；供氧余量{(capacity/aor-1)*100:.2f}%',
 '净径D37与中心井D6均完整标注；水位与池底采用第08组最终高程。':'池净径37 m；双侧环形堰中心线直径33 m，距池内壁2.0 m；双侧总堰长207.35 m。',
 '构筑物包络、节点和折点可由第07组CSV复建；本图为课程说明书总图，正式CAD/BIM仍须完成地下管线综合与专项审查。':'面积对应表13-3：水处理37990＋辅助管理5008＋发展2800＋道路16240＋其余57962＝120000 m²。',
 '8.0 m为每格净水宽；含3道0.20 m隔墙时结构池内总宽至少8.60 m。量水槽标定及余氯控制由厂家和试验复核。':'每格8.0 m为廊道净水宽，不包括隔墙；次氯酸钠商品液设计有效氯浓度100 g/L。',
 '压力预算：静水46.60＋曝气器5＋管阀6＋余量3＝60.60 kPa；采用65 kPa；池内配气可用余量3.477 kPa':'压力预算：静水46.60＋曝气器5＋管阀6＋余量3＝60.60 kPa；采用表压65 kPa。',
 '标准风量基准必须随图标明；厂家按实际气压、湿度、入口温度、SOTE、喘振线和噪声重新确认工作点。':'风量基准：0 ℃、101325 Pa；6000只为曝气器数量，6台为鼓风机数量。',
 'FeCl₃化学固体使MLSS增加0.238650 kg/m³；平均/峰值SLR=84.456/126.683 kg/(m²·d)':f'生物固体库存220500 kg；20 d泥龄对应排固11025 kg/d；峰时生物SLR={slr:.3f} kg/(m²·d)。',
 '甲醇、FeCl₃和NaOCl均为缺测水质条件下的课程设备容量；最终运行剂量按在线监测、瓶试和消毒试验校准。':'甲醇与三氯化铁仅列投加接口；消毒剂采用次氯酸钠，有效氯是剂量计量指标。',
 '单台12000 Nm³/h；65 kPa(g)；参考AT 400-0.8 G5或等效':'单台7500 Nm³/h；出口表压65 kPa；4台工作、2台备用',
}
for f in sorted(svg_src.glob('*.svg')):
    root=etree.fromstring(f.read_bytes())
    for e in root.iter():
        if etree.QName(e).localname=='text' and e.text:
            val=e.text
            # Exact whole-line replacements first, then shorter tokens.
            if val in replacements: val=replacements[val]
            else:
                for a,b in sorted(replacements.items(),key=lambda item:-len(item[0])):val=val.replace(a,b)
            if '需气量40638' in val:val=f'初算需气量{gn:.0f} Nm³/h；采用30000；6000只曝气器；供氧余量{(capacity/aor-1)*100:.2f}%'
            e.text=val.replace('12 ha','12 hm²').replace('65 kPa(g)','表压65 kPa')
        for attr in ['fill','stroke']:
            value=e.get(attr)
            if value and value.startswith('#'):
                e.set(attr,'#FFFFFF' if attr=='fill' and value.upper() not in ['#1F4E79','#20323F','#548235','#C55A11','#7030A0','#843C0C','#C00000'] else '#000000')
        if etree.QName(e).localname=='style' and e.text:
            e.text=re.sub(r'#[0-9A-Fa-f]{6}','#000000',e.text)
        if etree.QName(e).localname=='text':
            e.set('fill','#000000')
            if f.name.startswith('图8-1') and e.text and e.text.startswith('RAS：'):
                e.text='RAS：6台4用2备；1266 m³/h；H=3.0 m'
                extra=deepcopy(e);extra.set('y','710');extra.text='IR：6台4用2备；4219 m³/h；H=1.2 m';root.append(extra)
            if f.name.startswith('图11-1') and e.text and e.text.startswith('周边总深'):
                e.text='周边深4.00 m；坡降0.775 m；中心总深5.275 m'
            if f.name.startswith('图5-1') and e.text:
                if '格进水井 / 水线' in e.text:e.set('y','190')
                if '净平面16' in e.text:e.set('y','220')
                if '有效调节容积192' in e.text:e.set('y','250')
                if '最高运行水位' in e.text:e.text='EL23.80 m'
                if '最低运行水位' in e.text:e.text='EL22.60 m'
            if f.name.startswith('图10-1'):
                if e.text and 'A²/O系列' in e.text:e.set('y','449')
                if e.text=='好氧区':e.set('y','474')
                if e.text=='DN700支管':e.set('y','499')
                if e.text and '1500只' in e.text:e.set('y','524')
                if e.text and '单台7500' in e.text:e.text=''
                if e.text and 'DN1200环状空气母管' in e.text:e.set('y','615')
                if e.text and '风量基准：' in e.text:
                    e.text='鼓风机6台（4用2备），单台7500 Nm³/h；曝气器6000只；标准风量基准0 ℃、101325 Pa。'
        if f.name.startswith('图10-1') and etree.QName(e).localname=='circle' and e.get('r')=='3.5':
            e.set('cy',{'555':'570','539':'560','523':'550'}.get(e.get('cy'),e.get('cy')))
    if f.name.startswith('图11-1'):
        circle=etree.Element('{http://www.w3.org/2000/svg}circle',cx='385',cy='390',r=str(225*33/37),fill='none',stroke='#000000')
        circle.set('stroke-width','2');circle.set('stroke-dasharray','8 5');root.append(circle)
        label=etree.Element('{http://www.w3.org/2000/svg}text',x='385',y='285',fill='#000000')
        label.set('text-anchor','middle');label.set('font-size','23');label.text='双侧环形堰中心线D33 m';root.append(label)
        for e in root.iter():
            if etree.QName(e).localname=='text' and e.text=='净径D=37 m':e.set('y','675')
    (svg_out/f.name).write_bytes(etree.tostring(root,encoding='utf-8',xml_declaration=True))

# Clear annotations/highlights and use the reference's black engineering-book typography.
for p in doc.paragraphs:
    p.paragraph_format.widow_control=True
    if p.style.name=='Body Text' and not p.text.startswith(('式中：','　　　')):
        p.paragraph_format.line_spacing=1.35
    if p.text.startswith('图'):
        p.paragraph_format.keep_with_next=False
    for r in p.runs:
        r.font.color.rgb=RGBColor(0,0,0);r.font.highlight_color=None;r.font.underline=False
    if p.style.name.startswith('Heading'):
        p.paragraph_format.keep_with_next=True
        for r in p.runs:r.font.bold=True
for t in doc.tables:
    t.autofit=False
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.line_spacing=1.15
                for r in p.runs:
                    r.font.size=Pt(9);r.font.highlight_color=None;r.font.color.rgb=RGBColor(0,0,0)
                    r.font.name='宋体';r._r.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
            for shd in list(cell._tc.xpath('./w:tcPr/w:shd')): shd.set(qn('w:fill'),'FFFFFF')
    hdr=t.rows[0]._tr.get_or_add_trPr();repeat=OxmlElement('w:tblHeader');hdr.append(repeat)
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs:r.bold=True
    if t.cell(0,0).text=='压力项':
        for row in t.rows[:-1]:
            for cell in row.cells:
                for p in cell.paragraphs:p.paragraph_format.keep_with_next=True
for style_name in ['Normal','Body Text','Heading 1','Heading 2','Heading 3']:
    s=doc.styles[style_name];s.font.color.rgb=RGBColor(0,0,0);s.font.name='宋体'
    s._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体')
    if style_name in ['Normal','Body Text']:s.font.size=Pt(10.5)
for p in doc.paragraphs:
    if p.text.startswith('表'):
        p.paragraph_format.keep_with_next=True;p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    # Existing title and drawing paragraphs are retained.
    if p.text=='某污水处理厂设计计算说明书':p.style=doc.styles['Title']
    for r in p.runs:
        if r._r.xpath('.//w:drawing'):p.paragraph_format.keep_with_next=True
settings=doc.settings._element
node=settings.find(qn('w:updateFields'))
if node is None:node=OxmlElement('w:updateFields');settings.append(node)
node.set(qn('w:val'),'true')
doc.core_properties.title='某污水处理厂设计计算说明书'
doc.core_properties.subject='2026年9月15日修订'
doc.core_properties.comments=''
OUTPUT=OUT/'某污水处理厂设计计算说明书_0915修改稿.docx'
figure_keys=['图3-1_','图5-1_','图6-1_','图7-1_','图8-1_','图9-1_','图10-1_','图11-1_','图12-1_','图13-1_','图14-1_','图15-1_']
for shape,key in zip(doc.inline_shapes,figure_keys):
    found=list(svg_out.glob(key+'*.png'))
    if found:
        rid=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
        doc.part.related_parts[rid]._blob=found[0].read_bytes()
doc.save(OUTPUT)
audit={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'changed_body_indices':sorted(set(changed)),
 'oxygen_method':'HJ 576—2010表5单位BOD₅需氧量法初算，非完整氮物料衡算',
 'AOR_kg_h':aor,'SOR_kg_h':sor,'air_required_Nm3_h':gn,'air_adopted_Nm3_h':30000,
 'diffusers':6000,'diffusers_per_series':1500,'blowers':{'total':6,'duty':4,'standby':2,'flow_each_Nm3_h':7500},
 'SLR_biological_kg_m2_d':slr,'disinfectant':'次氯酸钠','effective_chlorine_dose_mg_L':5,
 'solution_effective_chlorine_g_L':100,'solution_peak_m3_h':.3375,'pump_m3_h':.4,'storage_working_m3':40,
 'layout_areas_m2':{'water':37990,'auxiliary_management':5008,'future':2800,'roads':16240,'other':57962,'total':120000},
 'limits':['缺少TKN、进水氨氮、可利用碳源和碱度；未完成氮动力学及定量加药计算','供氧采用原稿转移参数作初算，非厂家性能保证','二沉固体校核不包括未确定的化学固体','厂外水力边界未给，不作厂外假设管线计算']}
(OUT/'数值核对.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(str(OUTPUT))

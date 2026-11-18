"""Deterministic activity exploration runtime v4, Python standard library only.

All teaching data are original synthetic fixtures, not university assignments.
BANK/CATALOG are embedded by standalone generation. No model or network calls.

v4 additions over v2.x:
- New non-arithmetic modes: rank (价值排序), allocation (优先级听证/一天拼图),
  compose (失败复盘). Model still only extracts; code validates and records.
- Surface variants: seeded deterministic re-skinning of names/framing/card
  subsets/option order. No seed -> variant 0, fully reproducible.
- Report gate: finish/stop (or explicit natural-language finish) first returns
  action "report_gate" WITHOUT any report. Only report_final (button or clear
  natural consent after the gate) renders the record, and the thoughts entrance
  is an explicit prominent question at the gate, never a hidden postscript.
"""
import copy
import hashlib
import heapq
import json
import math
import re
import html

ENGINE_VERSION = "4.0.0"
import base64 as _bank_b64, zlib as _bank_zlib
BANK = json.loads(_bank_zlib.decompress(_bank_b64.b85decode('c-ri}TXS32l`i^zs?L8<xhlooJ8?o%lq_|{sbf3t-mcT#NhQw1KBrPDTB2<pOQM>hoOZcf1ztb`AOVmPcmV;5H&CQ51VHhI3qd^OpCp)TEj;Bfobin@v2fv9APJEat@f_8w}>^@T=P1{_{R17|MUO2a^<~;x4-VW*L~~Tp8kiuefQt{=PU1Z{<8g-?eG19pWg0%*i-kcz4Q9}9qsRTeDKR}yX;nd{k>oH@^ckhRKA#+^clWMV>+rfpBc-((&6|&4q~ND(3nf9#5(<G#urucX{it|W#<3x8MKmzDlukEr;T8e{!|lrb7t1?%@~1cYj;HDb5=5`KlNqzz23XMJrC()-{S}RslV^hKu`5=`sIH2J^b*VS(q~O^o@|UpHhb-(gnA;*LR0o$h+0wZ};85-Sc4J)<E}H_{9HPc|ea;?6BI9{x);ZjD^LzpNzQ2T->COy;u41&(*H`d+v4*^xV01ulxV&>u>DbN-mqpStFh^*QaQGXvjvuW5iQ+-CKoJDZi)o*UXLax(B7=vN4##Jh>a`!)Xj(^gX(Nr@Q|<Ox=jTC>5TRUrfkmm<Kb|Eml7fG!}+b?wOSuH0DCI4d!;<%rDA!X(J8)Ax+U*-Y`RH+Ei<}pnM5qX0w!eLfcvP43)jXzk7!C_kYk|fA3+>{fB-1j{8)e^C`~(#-B=2Uk>}EUp~=BNpJNVv%hcbkD80m%X7Q+OUfTC<yTAj{Znt68QE2vld|~D_RWaqXpx$=pyj2l!=}}}#~0#cyQ#u2RD8qCM^$oOrNhS3z7c;V$Kf9b6UOUhBkq@tR?!VQMaI$?wWRGfwqt5y#!8Kp4$`#OrOb}X1?W`J?mKKEE&D)!-(AODRN-LxnU5x@0vm>B&|w!VZ=dYGad&kKqE?=ou|WL>?s={B@agZ{*b5pZO}u^^{Lihy2vH4(J7&zJX%mgyq`i-o3*o~)@fPE$KWq74o8irW9Qcpjv%=$2#zTWJpXH6|RWtNldH0QtW%YC%dp5fy8z$6|w#wYtradz}>vA)(d9!;ezlX6T{mQ%Hx@|rG^`NJ}_g>Ha0q31dKBZSxDr<Vzown`kzTVp>q>@HxUHSG@c&<Dau3NwISdb{okz2Vibn3mM1#7%1Di<*$8x9Z5$Rcg3zCuSI$W^2*)PF{EWzW*7wlMs{NJXr}VPSc)kj6}wxE^gGSYCLtbQse&Po6#r65}&A*UB#vXp>!}W<-IApbB%;yOEqQrgyC37*pk=JNj+!ogUf+$Ndz-!Sr;H{_&<;8YmDsaiC1b_K0y%zsocgb2%xe^z`)fcq-WNKwm`OefhKD%!L~W^l|%X=7&q!C0RD>Fl$av;3mdjSjCvNJRt)#LL0>G>^mrXE1%Lk3^H2fg~skUJ$2Z_{+@?@kNREqkOUthCtw!~!`AZh8}6Y9E2V?EMv^C=AreXqzy3;jU#aZ&srRrIGI_ixQ@5#}d1~ZDp>Y6a&3xF{4W0Pj3hC7XYwf+=ST@ENwP+OCC7yt-W_gmfw{k@jAiBdFvbqjCe5dD&M_)N#(a_^^BueuX;pz>ySB@$jG%Gb-zb4G)>o+zShB$p{j_D?Ro=9|+Z51wcVwPLC)5l4(vumn2s~%5~P-<;06VfQ<a`Y-OPYiH=gk*D)iwKI)HMJ!ousqpf5pf6SWr(tp*l7N^l?u>}ci7*1v|jza-FF{4@9_d1DeN&=_Hf}%$uM`~fI3uS-i#%&)8QG**T7<#_81Gxw0Eb!%RGJut|||}SSLpv_^>=U!lS)@x=0Puvcs;c!=wn-%^Eed&?oM=GvcRKep$y-CRahJX+jGPGO|n%w0kBCNR%q7sRE9JZ;u276(;mELH(HdCss1&a4x>=z2EJ|oP|JPTBF<M=FA(O3Kd&2p2n@zsPet6U&h6p8XGl3WA!^n6OO+!B72adPkkP032Z%|owA+=X*XyeTyV`XTO-PWTD(uoF5Q-L>*~oMF<mP-Nn21}4UvoqqFZ=fA=oh@=Niij02&;ldtb_o)4dn+WXnPVRh{7JKpzjq3D-nRx$#maQJz0^->ru3zU{vIsK=Qs5Y(g-M+`va!cHoQ?)%>~_V#s8cYp7FXHEj9?)90pN|Uc>jt)I`-@V&+yL$jCoJRiC{oUQ(FP+aRph@DnF@8{|_&7nQUv~H2ebn#VsY+~FJ8J|4%-EbGK)m;$@1ebz`2T*WDx!`keQw?EzW3l!{VKD@s`rkq+^Mvwer%xo;WxD{Y94({%iMi`KtDbDX79jVQCP%CR(}p6un@8eudL!^{cRoS`L6-l>d+sRFa3Gh<2S~iL)?f1vswEoGgrj9jU9pzg(uYHln9#2H%rW%u7lc~BS4RXTJ8D4*LoG|Zsq2x%4CRF(s1gU)3cA?|3o@h>A~_W30o7&yH_ei^(Vq})r(MfHScr}bl0vb0LPuL8b5ud{ts&O$J(#+FCR7j(pmfGpMP<>-ac;prR(IqeRO<p9dFXxCvPyekB{%I^G$mDyz!S0PTt!m$M<&iP1fy5Z#V0DtNu~j@q1qo_4%gf&XEJz^y>|OIxQ7Xxc;X<pJY4_2fF+D%GVv*_j>L#C8?X^dynq-a#Q6SEk9ngzxG4*{(aqhUs`y5L=dzpfOXio!lS{mXVOUS8mk^-aSclK$!8?G(50s9EH@n&JWm%q1^q(~dIphjO9%7D#F!e(@%2wNk__ViU*7GxJ)pJyrNWY+Bq3NtxgbS*ee&T_ZnTv5l(Ie%FaL3{DE}a`0-13#R4Oi*(@~(|V$z6Ysl9sgg4l|&xkim^zWUAmzQ5cBfw`P|_sgkXuYOjv2)DG9c-HHud+)u|*zq4f|McJA|6_YcU03?YPKO^mt~&kL)#RJ~eZp>GF<PIph9`_DwgF<__O$YD6LK^b){NXFFB^pW^2%I!VMSzm=tqaWYGoLrq{m-g&Z=-g#c~i3wW>NtKN5BltCa@+B!+UIuw5-J*IKFs_!FdZ(&dP((RcUG?XSDp7S>E8v75Cbl{mdz5lqzRe)-9vn($hyS!;KXZfrT~BAaN9Wz7o}X$92c)hoKF<+(i~Gpgt<FXuZtg<PpoFSW4_4`~t5DmNjmh{_nDHTfX$#m+i4yD9I0ELErm&NGp#2|qOzVx~!qXO@0BfxIJMmk(72)hPGWw$WptZ+-OsC&o-#tvtOdKbf0;b?Ci#5$Nifia?!bDztQ-snBxm90h|n6<WH^RG{i;KSQa-?R936-FNQvf<ZrgQ`zSuN7?7dZ&zE8hVJxq-?`g+|LAS$=&bAi=7maA#`cCW61JHgNi<+4`DJTwThpyMVlRnO=0$lnNt}eZiZDw^O2dUxp(sp7-YpLojM*h(L_*7&$x)(OlGmXB<`<xooZVBNDELlc36fc0O-%(vrlKD$kLE{eaG(BX#CAxC5^KnhN_;xrPIDT~{ZDe$F>=+vefs`yKl|6uKL6<7-X+Nj$MC!6Qk67mL83bHVnv!NWj4+Hx>$Wwe$Of{HWQ`fYLX}gIf@Rmye$G%i~yOjFih)Wq+Xiqj~hfRA|&ON1(lc~BBXpLl7c2jNN%H}CF-9>0qCRmKQ}^tRx(X|{Ql=8^Qgd5mwX$hr@6%+yXNQWnQDGI&s0!3Tg^|$+tSsXK<v48fw~$edFAs~bTwxyMt$r!tRug5U64{q?s!u%C=d{mX2!>f{HhG`tzqJ3Kx0hg%vgq~1rZ4GMH1;n4C1BC3K2N4+sUVDauQw-k0->U++2|qlCB{Igj3~(CBw7M(w0ZXo|basYH}9(qxdUgGZ2i#za)|}CI+d2xfv17QF(ZS#JtNQ{kVD}G&5?uicCMrJtECGia0l%grTb^m5@l5dM897@q)c|_t95hb$`|4CJi;TaukS;_|w))L=Nv(WFj$oL6@@&^D5ybb3Is&M6FcHSvV5gSGzT~-O=7IzPSS+HNH_=!QXs10RLMOiwGZa&$P-N=5mt$rWI`$+H(SVh(1s7NgR1QU`jg(+kanel#Xf}Uu$UGadN@vVfVcUcaIf~I@%j}LHmh0aA)hUUcJ`xt6iNf3m{!LTK?*_*1vk~M$4~WZ+(TYUu*fRAGAK#8|^K>db9bfE;7hpdV0V5df?bY-m;W=t(8GN=zB=Q+qXTp?sk9Cb641-rXS5DAG!C?s3f13qh9R;7Tf_tjQeduP;Fp8<(3FyVH#mQ8zl0jd@oDcIU-`(yVF(p;dhKk7KX9Okf?i%k)kmYHX|F_gce*;;Ta>gqta7ERaKY-1CP0t7s7f9f#=c%Ke#ycI)+5Nr5J~kN<L?~w#R9IZk|*M>bT}4@LYSR1fIXZ&GHy=N7}R^>>PQsBI+3F9cyPp9So^V2B0K7Sss0Ct&b>Q)LGQAicy-V6`ePpj>yZ#1j5>64OA)%4X8L6viwwzP6B0d8<K>q^=B$P1%ZAkg9E)ZW^NvKl=5B(?}>`PBA<G-|Jqz!lcAkNTf}|Vianj0+J*emiTrx~h#^g0WG8W$^bVH(aWG%o&j$_S({&sg9^z>oj7}&`b+#@|b+s-{b+j%LwJu?Fb+s-MwZ2T(K4@K<YF!Zf;A+bQzR`7la!unhUO)MSn!b5rxuzWV$Q^`Kz&Ew2fK!YLu`RD9VQNY5h(9~ABBIYgU6r^83C<N_Mpw2HfeH0MDIel~UWl{28QU>JYmiiOA+37|rI`M^i#)YtLj)f&`&-H9G6^v5+)HE6rxIIG{IH^_JT?JD$#g^lqAIqq%P0Q0N1QpzJI$n}pQIi(T7C5U-~ZcZpZ@m5BF+gUq)&eLAD?{s`_JG1kI(-7{XcyAFQ5M5Q~LXzl8n0h2YSEkzCCb^aAY@YMLu$R+13V)Od+V_;DuGp(!sNmX&1?eWg=;3Ykuejct0O{B~%AQV{r}opAYp9THt{gL=EL_S_@e<`m_<x>C^$VQWJTspw1z1B7M=)m>ADY{}>#YL|3Hc85$aYPD@Ki9gIeer;`$PL#VAh7PQt!Rra+S^FSpW-q&IhbyKI3s{DQZtmUHC6)zpFzuI}Tb&0BVDWj`()z-Dv<+$su3n(A7uCw{zX6x#na}<lNwroD_I2*A@E@v}QNbVUCUSn=a6`m-6Q0{CgpH~3{1WJ&QO@s-Z5!FG!P$k$;SZgWcfkO~8K?q011sGapmqatuRPRG1i{%$JIRUR{e^y9?5nO>QbPWY5<<~?pB#uVbvq5Sj<g_B8T|Nm&R5(I*?HFGn$|NtU@TzN!ucPvZURK_H5(?pGy*vSvfHZUK<;1aN|6K&Ae{T?;=%;`A)8~Ks!>8{fYfs~&-~aC4KKtZ<J3i8H{r(TX``15w`o}*y>z5qGw0A<Z(pgGw-4^4!qg++j#!;v`n(L%7xUAn<qT+BeI;U3QnVDNsgJBn+qe}7+-INJQ2OHKF)cSZk2v{m?Y_2`}@b=x_2mj-n|M@=#y8FNC8F>G{{^=L*cmAUDpQ!DB-MUZRefVEL|LT7};^45Yj!urwh<#&C46E1<%yyk8Q7}CT0ugQJX}`Yuu>F_UjtES34LYR3$poO@`$YV^LH29;=zB67`n8s&y!Tai?@^Zy8c!YDq0hT|T=YD^>vd|T_wM%IW9N#xAA9=yNwT&_(f-T!+K;@~hpbs&_w^0js=VF)%g$@fVtqKd%{SIwKqb~`=SeoDf14A0m<ywtHSBqj5`;G!J51LEUhuSM#JME&T@L<{Tro|&Q$uT3aZ386Udo<Dl>=R_{TBFT){Eb><K@{Mv0+&2Ln=krEv?xcho7IuIpg9p{G1>aQ-klu+sol|Vuy@3T*l)}5!X)Pd+|;&fUo*{dhUPS_vm5IacrQbWlPM!`F-0Ck$J9?30&|bP8w~a6&N~(E9iFudj_4kM&9ttPAqZ*cj#co(EiICzo7qXWDf7&(d^+Gy<<agZ6&2o<(|RuXgz2of|c<7V|fPn1e*^g2F?7Y;ZM_jy+gmXcQrB(x0W5(TjC<W>};8j)T37V+bsa1_u;^!{x6UO!l9S;u7++pt{=ybt~v1|Y}R>lq~JDU9^!tvVhtNm%IdfXb2^Gt3me;X)JR-W`$?QGiA{~aG+(A5)b1xO&qR6QDGB3dd>mn<bQH&y<TSanrtoC><=i*G8OaIcW!dwUqlwy4h~uE>t8qPo(>eoLbi*pnnFl$Qo)Y#X%Gb-yo_=CJKQSN8Qjm|NiIZPrvzFM7!^?Ic>CgslU0~4+jj8Omk)JvahVTp4;S)8M6NW?7smgL_VXLf$o@i#%Ma-tl1&OpDAr7u=<fz@62To_snBGB5Mb>LZw&+t5nM(UbG?#|-)oG2?$6=8MitNHgt~ZeXW2t}p5$f;I>k+2n=KkISn`pu%WO=pzDzW|zvKi8eNX~;b<kvx|!;>mF1`Qk&d>dm(Sg@doM>>sxCvUC1G<+|BDl!4>ATg7c%mTz_L~0Sa23#aDPvnNCaGk!+Cr1D1OVhIQK^nA@8A;THPlR6>k?c1TxMv+6Qad@Ua%bV#HSSl$HO8h?c!;ilQ!8iTiQ!+jmM4hW2ofu=Ea<Ri{!S$sCORT+g!{3+sz$dpiQz?%P(xv3mx43BX$HS4XZvr=z5eaf_dorQPyg_*|N8<pa_<EDt7fVtP}TRBfv?>d;L(PTEU+f?tvmQ?e7(X1&B$VTx=6CCIv9e*F-`MdGJKOn!JN6Fv8c12tHrGH=1H9U$jpxr|5OWOB*@Zr?||dg$MoY(oblmpb8)Ra_(X`GiY-}_YxJJ6_Zp0863JN*W{juR2*VTbM10lm%8XEN5v1Sqt`lj~->-ft8?AY~#hKd2#a=<X&2cv`Dv8$W!#u2I>cabvgLysM*ki&32o>^YjaSREZ0s{zN%2tmq%rMNxyZ@6Zr=mPNUiUWMCNfUrZ%=<2==%#$bD6w4;%5E@{Q7p{EDV+kB3ief))kI3u77TLY4!Bd~jYe7dJ>4I`oV4`7w`^EWn|~kAC&B^o0-dn{f2wy?5&36FFzEaZCbB;5?Nt(*W_~SeOuu{i6{%M3P`$+S>K2=gqE*qbIH=M}Wg38)DqDmkA%>>rel#T?f~>tM~>n<k~Lu!jF0z7aMC?=}%?%ny%|7l@zTU5KkPP){kRN>PCBH{x0%P-=l%sefN4!bbP))63X{wPtTn%x^I8OL#o*fNnVXvW%rPLtvF`Sxa<w8$9nViD}#IH$X@M@fRx0hL{;?SQFzJ>rK|ViXh`A1M-LwK^@D4F@f}J1%)f8<_j3MG8rwksqn@KL-Tu1g_BWg#?}z$lKR9h?^T}5aGfgS92;#oKPX~Z@#oFD6f;hHh?kwTt^7Pm^h~=oEX(8A1bo>mz?7sW(ji&g?@%uYDfgD%tuqKHh>^W&B5Zj^aCn>uj&82oo5OE-D=RdjAUHoIF9h}C6&p$Dq#*sBFnKkB~AT=>vXZF+6ldswCx3h!CA5tR_5DH}Gwv~4c<cBG-O_mxtQEbP2^^CZyxCn?a{#GvF2~H=G?CGdbLpW<5%u8q;LTQ;$Y77GpPB>2zmMRsVyoKZFhC8b%>+9(7d-dacuZF1qxp{6pY*#c<Bgu@b#0)Mg2`#yp#*DbEII_6YxzXd&-Nij5lp#YxG@(VGSP{#)zFHom1zxnBIy8l2btdkI=Kzd39X<t&yMS5=Z(RSNRga4cs)}$@pm#P)-3;!1{Mqj=3hOyLTHNV<_~35$cee=d+<P?8tq*n0DC?+;$b${J3q+`E$g?2QSZz|wTH5vf(f1oW{pe(!zH9LHHsP4N-#r{S0f4oewhCdLI;d)LUqL<VAF_&bm=#;=nx+H{!&Spdrd45@z#Yl&b{Adke;XMt<<`y6*p2p|2}tRz{&pR|AsIJox<-`mv91Be#6U0Xo}boV7tPQK){oC|Of*>tN@XNKSIqs?WC-w!iA$pv*qBLIGI`Bo_7%8o_d*gI$vlF-A-?n4NdD6EL8k&1X-Rn{=|ol*5HgD7>W7FqUn&IQs@9-?tb?7jEd&@nL4t7{fI6sxV>AKDsYus@dX_b720N)ynYb9=hO2rUfN3P(&qPINvVn7XIj3^rDr!3=_SE$@_?v&7?QH)QFM*21V7VipJL%Kusq-_!xitbMc-0($gWK$mQ^!|jO<iWoq9GRm;9ag}8QI?lQ_py8P0hsvOY`+14jyM|62U@SI>ofk4C%6p+;aX1@XBDJ0ulg~8x=J!Qse~!f+1AlF+r+QE@WT9ON#~hPH2iS8KP^6U1=mjF*%!1amD=v<*jFf7lIzn6#m6xa{riWvrE_Hh~7*tp&)m*qP@V4)Ykpx)bkSRFtk4aO@>4OAvHW`8#(D@Lp+B!0D~8ztMJiA00a&utw=#r3Q53is|Vjn;MZ^oVYBo4YOgEub}mKC=X?4@7PjDh>Wjj!o@@TV6Lo$Bb#w9~a`c-zq0FRl3Ajf&6Lq;9Y%hP-iBVtX<S5r2LE#}u!p`+(h)yhCE^v67LV9(zfPR91N8sNl|LfC#Z$xrV5smQE|LF5i|L~b}dd^dVxKEs*l{>OK8HjrmWcaRuxG(QM>g(@$c>74HMQ0#a*Su9Q=hlfGArM?wUOx#WrCd@p&_aNkVLCHEY7IYCu|qW+7Gs!7jDS$(N8ob7J$AOY<9DtCO22pD&zOzatY8WnBHv847~1imO<OnFL?lDdZXP`NBWbxR_C(RW3;Zx*3z+RJk=`BKD0&{qjKkd3YT8^+*AAG*3A9km6V!5tAYPxbl)=);B<akOJj^3UB4>^@f^k9Eb8uQWn-~)}epkRk8)o{)s9&O|Nb#2*hVFMVWDWVv_(5YWtCK^qK%j1kJ$XG#3H7g}e{_Xgy0Aywqt*&$e4K4Rhwd;l4-KrW2GLu(bL>g#*JrZg1)?QO)?{m`IujB)aq)o6z7%2-QsG&9XF-a1F0{omJP|OE(l?Yw#Go!0614WVFDq!X4{U9LK-lMeqeco-p#vwUp_C8NVxSF|Jw+CBg3wFZMn{CpV<$1@4$VYPeE&3<W_d#rj}phA$&?NkTAjdKHPs0Pl=BB~IA)GANlm~CPmt4<ogh>?$KVw};j$h?+k~aIrfJu}ZY1lgWQlcCU|k9brU_fk4FV!#+9(7}B6`II0J&M`4l7;*Z~-XCJvz3Odk`=Ai`O1p5NKl>A{s71M4bK?Ic+6_o;;GW2jzvQ!h)p%9v$SGLNx9jI#5>NX@RkJV>n%(t(ZD>UYWOPs%t&a`bSsf{8F3qE+oFXHf7C6fBNlbpPvCrd=snOFU|vcz8fe}6UbW+AN7CR<64`dv6(X}tPoq*NR1;e+oecX7uC{`kzY1O!hi@B?++_I=mH3XzVg~8gxdIqmJ^bDx|hgaIW|hbuaqxXV=s)6VtF>Hg8Q^iH`+_NoP6a3&=0}E&jwL<l=d;gRR_aitC$uaBUju<@-sXNE5<$|*QmDa53;5$X8$P}9B9wrYVO^jJre_!5h&0j_LAh5lOgEk=TcTNdUQ_bgCg~(3PJf4;RY*Nv^-wI+&9{PChKP_n=1k~Q$?Of6M%`w)CJrib2&H#AKi;O@F-a>IKqLE{Dk=Bi(N^ZPB~cbjqqbCQaT*h^B}QvKdI7NxKF$RVjpmwli@E~$%Jg0TyT+Y*$n6t?^J7yMEHpHY}Aa+0GH+>NYZkMU|3;5a%55HG8J)fk9Kw_jqQj-X?bYXp2S=5CS~tPeVF-raH)7WZ3))mA~7t#bGA>xm6z1A0_*Bbwsct3^9gOJY?02M99$f~Juk|R=0>Fsx1^W2tdhM<0yr@fY<6#cWZ;pn4yQf9of9jUgz-vTgWLq$(AR(~rPRFZrM@(J4HEKaMl?n6tcyQ{mE1r8nD7OOTAm*fz0D=nVwC46t=X_<gjzjQhm9qs?Ok^7gmOFMHP+@yma$e|LZh>|Mxq`4sVnLgW6HZGm-RTuPR_TEtWvDNs(8q*+ioDG{2b^L1H<yz7%>%Gi1@41fJDAljg{@-VzNDA9Ml69+DvmfDe-Klhl<WQ)%jaa0P+;&_00TmDZ8X;^kLSVo{+lqwA9w}gnU@IlO2VpeYpt2Z&t7&l4Vt^%LouZ6}~&el{~KAjAJUR>!&EG_mku0WkO?jd%C}A5;uROU2AyE;cYux3rDctyzw(NHcAK642==7w$fW_a<-}0rI>nrqvlqgrf8+6?f0oKh=P)AbS_moNaOaWvWSZw4;oV=^lxhmISr-C(@FAmalDa+e+Nt00Qx?4usW#xFX-QPFcV5CCpU>Kz@o+DA}r(JXsPd~fHE#$p~7hr*{K)tZLFP9IU1yXKWP8id3sseQ?Mt+X3u#&ov|gWkaPzpB+v4gCH*Y4mfkga6MM0oEEN~ZD<jm#*j%MQ-GSJIUshM2YK}-zzQ-6BclRs#j+RqWBc=R)3y=)`@?s0b5oI#OZf2U;$IP$@e7I(;qc+E1nJ>rft#gQ;u0x={B_rgAFARSMHe&yn1bYdvqEp(;lu4T{K@>>&%US`>FA=NS$u1Us$>PHho%QOdnPO5Ug8FxT(u1-{mpR-?Mk<-bIZ3<BpmZ>AF72p=u*^U#4VM;gRW6CX9&9nOic>n~keNQHNNmU2*`eQ2#$9M$B@^C{%;l1yzvR&unhn$UQs(GYt&L6-sqC_bhuVfbA{0VU<|oakj|uUYhd0c^YnkmExQAZEIb`0gBOwL-@|6;a7uKj;P9$3)Uhl4tB~uk>)^ZV*F2Ih)^*>1*BYsEd%UU0V*#>GjeHEJlFnFzS)^}734X21&aiZlB7G>Zkse|?^6+WQ_=31bLhVUGy!&z}y;Qa8H504$6RnirkS%nmP?4Bgu*MB=~)_wwPrdxKMI3?ImE|!-GuKnjD0#%Rh9Sheg?OKCt4sTa$ynEmRCoUN9(;gQckf_&O(!6j~TRA^vCby7~>eaI3J!_{aBdwTShDQ=)%Js8Wy=EaP$$W*YlnPJazh9GA0YUeCjcYH?iQpVUpkyi_mcBHyeM*J`2VaLPlIlRBtXMphL3FgYOTZT$jcZ->Pug<KhiHtMk4nulK^DmNIXMcIDs#+pGNz^0WQ|qPi={|stYTbNx}%wUqV_tCzp^)`!;VB!W1F%}vb^%xcs4|!)E&L>WApVPU|%M8jUyjX0wC_u(R#LJ=9H+-USuKIdbSJU#z6Jj2{ycgz_s<D>CcK|8yz&mGuXrimJ(BwtWJ4lie}dS%WGY7F15Q{K*wjw#KBKCJoH6b0kpn&xF(w>;Yqe4Tuy{~He_tFMNszX0`=l8Ahx*>tzl&zA>6FRH9he85yk~CFRNdrR7%K4k>PREFN3bFq5*m%$=|{=*V=#f<1>(HI>$wUNF;*?)9fDX#4964e6gNZ4Ay$>VJD}(<@q>jM~scy%K@oqGvVMdf0;~X!D$%Ud2&JzL?wfwB#{&zrQkc)jJ8}Ro2{Nf?poKch@E{{p=}(XDWYpFZv`P|4yK*9C9_Y9e%r@g!Ny0JK!4AFJ|fZOJ5IBCt*f!gC4hpG78Ah;!D;YK?ZPuyyWRxr>NrLvq}ob1jjWTj&Bjh12KLaJwf>A4pT;qs1!H&{3Xo@c0iBRHpg`2eP-l0ROfS5JB5xAJxr`7|#$8(gurcv7&Ck(r#~C;|EKmOY2_-fH!VjFVpA$;#xcZYf<s}7#{XKfjJ@<S1zjF1aY;5KT2P=(S;o#AiYtSI_Zp`lKG@ge^GqP(IT#{dxGJe!NnBGxqvsQW-0od%6R-3a^lH1DqNjzO$DOK*B*2CIaw1WE`?cm0R;7OwE*gL`63zP~W)QnjxAREDQ9*)?N-QRrJ0iQo3^w@|T{`$is<#=@2#8nTB9;pLsY=`!cUhQbdu5;HN9r!1A&}F;ZNp2Tvcmqd<A4-~LNvv&+ZC^bfEXZTSjP%&-$#uB`rTSNH+HYKUMMrp}v-*)P`<2cXu-&OX|MBskcN_5y*HyV-gvJN2qa8=DdUELOAteyoFO2*$iB=}k6fDYxC}lQf=tkT_=lG(eF7$Z!yIXzVxV;W3>R#`|hjcufx4PZO37$GSjuYHkK#IItvZ@5l_2K!=HBDw~*7AHL@-taC=dV;3?&fLN?UNI(o2-mzH7fV1{BjPNXS8!diliYSYDC>SM9sxf)rF9(HSjo>w7SIWd)&D^9iVtq_^glU)!HKpkAZVMrEh-EnCgOPl`;`cZh!ruOu^4l;HVoZ2ZhKLG_7&JN)EsA1w4O+4Vc5PYv$FZcP7D<SMSfe>_BR6l8oZ7Qp@F6TIW4KBJMUiCz*IwF_mZ<Wk^iwu&9#p%4yK<q6Ds>p@tW=pRgzNkx%30l@T*JYbzA2)EfO>Dok6cc?iKeVe5&3svNY^!CYg>AZvGogl&;N>oxq|S1P-G;pHFdoK5Rco(_u-Njd}#f=?QHC}OlugI^nZSTRf22-Ab~Uo#)K^#LlGKy`@W4Tsx$42(U?Wxou?B5FKY9pSOVk6oAA=k=2l1M!dFUCdl95#Jm%SK76PnjPM@eO|fx4PAO`Cu?{@#?rpEto`zvW~GskXU?nz9b-*~Na9jLtAQT&U&HVad3~dlFX)_^{4Z3vr4OMlK)xXKTard1XC>2L!K<M3k-aW?=Qv<3+<>@8sZf+k4t6w<!J#l#ajFqcBdy7d)arhWdKe*;!O+9hF0nObDR6QgCy;9H)hoEX%<UP;U0E<V_M(f5TV>pjQ6rBjPp9ez9Ld6uQZfrvl6UBAE_Sxab11IC3yJilG%CTJutawLb7!+WrBZRCv+kAlf9`TOQu0^mt-7z=_~+}b_{Ab)J%=jJq-A{|#7&OKG&<}9)ghl!-YqyZtvr=a$KbUjZ?Vg)Bu8=w@G@lVop%F?Q)buoo-C|2%}YAFt`7?;M)>w<!q*9%z=R(dGUJ1CvED)!oXWvR`NsVPn$dN`{~Q7Q2r9iWSoBqY-=hb&zUqF!rO?hEX;)?!q*Hd?E(x#W$QH(|<u`FNebWhFKYN5M^DRd)U)DDv6NdxVK{9-)4Lv_{QL35Rsdru^c(reSC((sYDOjVU%(xCVE_Q_o$0R$6O;S+qhNNOTGm>nCse~j^A|j61feQ6UQfA2{D;ZSzb@7Y8q<+1Umql{4R13TKM%96*f$?10OsPy$by;+Yd0@I$P5R1H)KXXLLDoM8P%N@W2i%st+s5{WHb}~<usIwt_@lv6URO#HIH&8AF)eJ0kR|xLCZP|Kq=_kVXT$!nwulCI&0$Efr={HZWrW1e;g;_CdRj@9`Yz*J$3RP$96M*68}&qX+MgVETfm%Obl<=8m)<+>1sWY%wuU<$-?yt<c(+Qqm-<35@{|H>&0r@@SH(6f@8nhHnMxMeRwrVRWTldRY{RWssNnLsHH0v7&zdnkWgJAzM6L@l>8V4tG=zVZGUHaE(0&rHU9V5;$ZPtp<STft{Lf2;s0>c~3v<s7v6n<u;f^{VH&=p0tyOl~*d3HkJ2CXi9EpF6*nalNP}bwBy%JaLm2fxE$~#W0=Wg(ncdomw_-PZ_G#kO7EM@yK<G<!S7X9{dGwC}1?F-L*3b)3nz7X&U=0bSh?Q$e(#DglZOmYC7EQCeXoZCz5aLe-%OT1WAMIF#^<+6JOe%ue=xnP}vz5y;JetJxMQY&b~EMW_s@QX2CAg#<;NDZo@bEA-LCB;J3*tu+TY3Gly$e~>3Uw1YbColKuz4r62pSS<K^Fwy+5FlDP&=;nSu#aiS*&oxc%KWPLQ$*P}CN1ZBAKzXA)uhiDd<@wz6(+f)c9qJ*1<tw0B}`ena7<APNDV^IxsZj_uYl77m#`4=$3|*MR{LyF5~yBAj8^s_3P;CLHh9*O_)Nl{!?T}ElE*-{PA7xl4JUWotIqM47inbt_{2W6r*+J25k<ZefbUMv7mvQWRdWFx!CpfvN1(@T+)<vxyLOJ#l@U7i=62r9FQS?@m##n>XOd8Ixu#il#tQISU~;H(>!m^vr2xm*kj!*CegD@T?aCLG^4&CdA*5<F3V+wR)ZaXD)Hq1YcOd!c-#iN^z;yRNyeZw$qTeUBW{f{J^9yjzmHY^y$K^=WTAomWjUz@x{<@tE^}bb{Q$=riIZs3Bu*SAK+BsR-4h_5-V1xwFvj7a%&Y~12sMZZU2b32Gh|*W=kN1Bqj2rdbS+RHXR~_xY>gbTL1IZz9OxeEs@DD{k9V?lj`N-O-^p*-wsZ8@?e%P9Ix(+gyn>XQNTOKSbZ%`J!6>DMm1wn0lTCpW#Gx2^$DZ6MN5$Cx`?i_O~ubz(6UF`Vvhjt&M2%extk(K#X=P$3Fph6)lUDf0iiRUUj17!qt!(06}A}>QnE`nrcg-BYn(_9Xj(@KRFamZ7bHdkphN&AVDQ_1p!$VJXEix@Z>I?w9T2D-&|kjRp$g;=O0a}mUiQ2Iw1b*a(V=Bkjl%k3~)D`Lx)XU$Cj#S%H#N{-T-Vap2$=bc?LLOx?*SSXBL8v%i4zJ0`lde^MfW-04`ceC6C0@m0Ib7YU^X>E8k11`McBFHJd!}BAW$T8z<nr4)*p{Pwr5Gx&yBZij2m8hnLJE;Q_@z!hwi;&7wV5(Z0TdxUT8Y2;~Ui1%!tz`1lXsRwNO?})DfD-b*HA!|Ouu3KU1aXc-Q^xF?D$XK)G?ccsmf?z!%h87=Ef55rI3lu;mUwg0Hp#=nF8E4h!ohj@noikA;w%r{sZ?2WaCJ6odt6$Zu9JeL_Kvf1zH~$@AODna^bK**?e4q1U-VbDpb0dpZP)@ja(TTPwg{be>0rqiSya&t7<~4VSKWdZ6L3lqwS`pqwcpzv7hAl!vCWG%WO;_+&&dDiggpC^mCEx!KE^+;a=CXryjpp9wes-l)srQzDL?k%I!o!aOu`(>^1g63o6R*MoT#ljINzAS2F^D$T>f}hJ27N@v+FtrBvTm5N>Us886pMG=$yPFldFVPYKx0QZXXL@Ee{t6hoImrCq8YKZ1iKpA2C9HK^+`Cj~$h<SIZtc!-n}GbYQKI(y1lU>E~C~VAw1ql_$yp2@{p7OIRve7U64lr6u#_xbo#?4n#sFF+WVCW1}#H`X*b#QH%pPPrkllgO5>Sp1(S5MW^uLT+#5X(;X|1g^5@j(>^4dV<>6wEDhJ)vy`*E(!kC2w7%uE<|?>NyxZNk)VEZQCc4`7G0U&%T80NhrCidC?a-j!LN3xuZ3H?05-2ZH<lC&1aDsZ;M+zR&idOOk1v%3nM54=zr1WxgE+H+p9eM@J>nmhux2fbtlAH<lJ^9gP9))y2lh)E{F$u`U$uk;Kjk=anITypr{hq(v`l7e{VJq&g#~)I@>_UsKGiwQHYQbA9(^sRf%@>z8wG9z170TmA`JRh6og_1pqgqYD_D+H{p)oQ^TtIe~MN}zm>f|hm1;XZq!6UuGrXQ{eED<{J-3H7ioJ!{aV%NvAX9$;Mc8{<960|K`J3?YSbk?Wh9FR)={jqIjmkZ08k==&OGtQ_@a?Cg<qS0x+CT4zua}IFs=83Ijj;Tu>)7M-(rYfM@(?5LrFQ5M5Q~LX-)TfskI6ffK-ZSv9IcTgjY5_1hylMyQ?fF<-%asb#I{B!76+ueV>84(j{F;?atHQLJe5oe9D!kv(jw~@9?VUCMy($3`Mr2R<(mE$;dW*iH^<Cazc?HH9xp2xmXeBc=4nm<PD=M$GXpHh`tyN&zT6w9lUUFI6z8vcdO4b`RolL38kjjN=3Z;YjQa;on<Xs(j)VdIJ#$Wt`l*j^c<lsVi?VJp3ayEG~@*TpEB$Cn4WUB5Ma>6fLBI){Smj@6qzJch(<h=P}R)ts9sFwr^`iwiMOohwy5$xW=aw)T-4u<WVr}BZ8t!vh5MrLNDGo@^kaa5qOxK79kQ2{O+!LAd~TkrW`D=d1=kv*x3<vJmv0CbLJLqGd1H1>2JQVXB`7AeVjJTkB9l4bWKS*I)+s0pD28t}wSRj+@sII)tYw-afDxnkSNZ^7kp$ecS=2Vt?{%ck0PTOlr`%qC6Io(&NWYX=_K`sk97m-XxN*(_CD6iRt?zxO{M_1t<W85?;&ubzYB=Ij#35l7|LA%O%DsLYBH@`DbeNTv%Nxa4L&O?Dqoh&oG?R+?LG-Ha>>0E2p{LLS~A5$8o@jmZS%@X`#Vjv)4H!fOn!Na6R|1hA#z0#pia1nP2Fl{v7N<YFR&V$3vV#w3ZjE>ue3XLenvCbX;)B*8XkeH&S^2L)bu3dN#0A?~|c&t7?bLW#t(XC`O==80>~^Q(y5(Z6{XbTmiW=fLI~kf>lEK`b0Biv7@jnMm}vtrCj>P<n?d5p*C9L?#z68R%@{b?NG=`IFu77@&D_CrcN{&7YhsFDE9v*UhBw?!#LTzwWtv*9{dmHgm*<b|d#hE{!i&kfBvzAM?bFTHO}I8_m3_dnGrm7@Fqc(l_CkECLem3&%vyq&d8ah35n<bmzns(q1r~IhvzpP5*?(R>$B#>Gd}s-r&;a{4JeoGQLrp+pl?s$@glrsZ_e`=n#L(YM;^rak<)btLIenf<N2Eb}|g-W;KQA4OfsPFI~4^>bP2c>jQU0#BW`zzSUWiV6~Nur*AO!W}|2__$E`n;9BnD6UJ_AGBiXL@W`rbP#am*n18bKlKM*Ob>_6AR<uAkTT<XjVmq0|r4?z9WCGR3E#3~v2CBD)bA2}M3oz$&RI-9nYfZ=s(Z*EhKMMF&xst!`(2>rtb=XmG4$f_t2yAH@!Fj9)Z8E`>8g@&U44rRqIM3hvQWFWV6a@82676@_(bBUH961>@*HL-M%Dv?C$4*9T1+@@nuh~H;2MR^#2%imdn7zl^-8bXoO#|8ZZpsHFO$of8xMrY~be9rMb}@HdF@h_-04C6jJ1j9Em}0{$=B0knX=+IDw}s5q3;Kz9olK6?2-o8Rwj;{5JAIB$Ei1uP=bCy12|IDIrKwA{&PJo(ai~jtoOr^>KPQF(mX~deRV&V+bi_;+K`E)Cnkqm9_U)BDOPb1h)*Xs99amW5JXX6|YEC;P$+;)zJh_pu*5X$g-}|5Z?%#j^(H}nh<M00CQag?Qch1;Z1#sPW9`^M=Xy!NS*tSK)=iGyxLuE2kj*iHUmC#nAzvXBG-f^sCYHAj&)Py%9uZfg&D(^USUC~6x4I}lE{=$M~qx7hw`lz$=C<gNuAvO}9cb}--Gmr`vrOUHB`ro-dWAAmT@WfnCov;$3B(CBDcT!G6=bqwk9~IuJ_CcD0ntWM)HiI{5RHI(y-GUbzGo`D#HX;{%v^zsi6?>*Jq`KskqsZ98rcXA8a=7qL3Wk|f*j@&DTbJfZE|V~3Mi#3%sLvi*BHiVU-$;Q8zXy>CHERROmt-hnl?OTZ^p=^R=y+*zGIo2l%PVnWFvk9tvFmlkY&3$KvQodI|I>LlJFCC&Vqn)KOCGWH7C<PDA+L1j2hG0~Gba32YR#A!Bc4HT$rp8&497ij%Wo>*yVg}V6LI5J#W^dPmb=u+192<lK~v^xhR|E0mJ6s%c|KfWX_czkZzCBDt%l6N2q1DrPE0j>UhJv48L2%?<=G@r*h_1FWYJF!EPMegSCKe{xt+HQg&MJ9DZeU3HRX(4R+!sy<5!&@BKWnV^H&`o$_3|3snR+2MMtdWMHxvyx^?d>$QZZ2LUj+P(i9)pw&=Lf9G^@A|2lh>)~oXa;Y%Hzf1T~n%N7%9RE1}8rXw5T{R>l;)LLR4KfyGTVJ~huZ$G;Ch@e34w_w$sA2_dQU8CdIw1qr0T~O2t2P1e@!@k7!*ObCtid%we^Z9+9^(Y^bVupx#%;aQVQag!l&kP1R9`aqTjv?MHu<WLSHu4rfuu2lT4P1vOFHq!+M1!?LQ%_o6QGsVjcoJD8#HXe<jQC;&Fox*tXe)q^os?2p0-!p<3^R=%0qoX^J&&SjhX*IZ<3C~U6Jzd=e*gP_`|Q)-o<9^ne}H{{=}B8e?e7@C1~j_;@OW^o+qDR+kG^f^tnq}2z*;jS)@a<WB-YfH>h;rH<pptsqb{uCm>C))(xDThc>T~>rXr<7!We!m?M${jM^dX#UR0?AGqOv+m@7e%S~+i=wpto<Po#mos}52|U=EJ3{G%o@#RX$xP(Dhp!0xfUVJ33+Q*$~B188ENI+22wLdKEUD(Y3yjU!R=jzHa>+;2X-aqVZIWIU5!e+c_utignfY*${N{fb70b-p9Hb@gOW47tW)ghs2jSgT9`jFrjuWbFz5=EIv(r2Oo$wms4t*Q-<OfVEPFA!E3C?Pu;8Why<;7^^+pXz1Ys$13Y`xvM>NReR{X);NY6KWhPGztQMEKK1CD&+jB_e8I3;%xb!R4HOFYV8sSZ%jRZr6mui2B0LLRzR;!h<*hvj#1UvGs+D3F#v1Ie#)QA&9@AS@J<nxKk)luKZ#vuSvW8xuvGhz+pw{2bU(4mKO@=C@^3o>W5fXmrquT)`9q*2qP%q4Qdiq0j<2pDTB4e(DxzRsvUIXi~(~Zk<LIIK13o`x)JZ8(DNyvV_S;;>@gsrMV48JgADU`w@IWRtM?e3H8C;QAP?~o0xDfATl70;1iDymYcwI~=~!y@f;24`9lPYE}vseqO8mkLWD#R8FHOXkiJya(7we5t`GM8U{zLs+MSQ>~ORSDTZ~8a1?Vhz_kYIsb%M9o=)CLOwg%oqp_at$T5?AoM41-tz#VU-sVbrc-(AL4V)9zGf!gqYWKlsBY#S>*@5mof_z1&KO=&zKqJyWmqfaM%BvG@^n#6&NfA()1xXk3r*eB2I4t<nNlWFj(CuITuVa%R_?u!r}|O*N$Os})5n)EW;S)<rTLN0c5&S?BU|=(CBV(qR!hV|495_mr#8y-VI!WSt;L_g0R3)m<t3G!43Mpr&*Uk4E>?cb?v+<YNGgS@KRI7D^_+umZ*flRmWjh)?OuZBWr^km%uT;AE{w<@WK5m~&aWg@QNd|*{FN#^CLZMus(2G*RmF{#4ZYPP5L+^y#*Jwo{TCs*bE(dD_XtqBK@pFNBqbLJwTDHL(|}jYAf7$~)R>qmuZ+rhvUWC0*);8cDVLMX9GZ2+Uq~Cvqsvga$A^mfnRnmJk8t|(34{qAj;QQ5fe_*yG+Q0dDS3c>qtp@~+Z|MiE%#JG=>=ppO=jReR?($k23)&Y?6f4UVE7!^{1&{9IWP-R$=+=_KAhYHn~YRYk&W6Kc4{mqxkD~%R#tZUs7}MXSIW<nio<jWB>)?OB1hWEF~784$DF^H*14LCgswYMAuWsU4*oT*2d=)|RIL+!eP{VrnVT`Xxd=wq!Siqr5J6k=?Oa;D1=9;51nMzr1%vuC)xc&2p2JU{i|fj4SSH4;muW%m$!1R}qG$Nmk<t6{gi6d9xs^+*%pfX8<P4mJNtn<t5{(eRnjjjt{sz?HM`H0T&n9&oAaj4BI94%AKo6mVOkZd%B%ZS=+8mr$qub`@jGZIMevLq_b$Ez$+4Dn)2hp?_p_{V091?nBR4Jrf@)Fden8h4Y8->Q|@rwjHMfS{C;Pl2#M%iXQZ0v^Wv7uf4@EF*q1?IrCwL7BnIV+ijust?qJq>E@d}zZ8P9ovoYRCw!qxwbRwXOK1V_7OZDZkME{Nj9poXYbfl64jlHN1!-Je~#)p7BC9GhP1nvw!{U^9CSi7eG8CzuXqn=ltS4VBkB2*uL!Vest$Jv?h&OLTX1|t)R4<H-9F%$|Nlh5e|~xn&C4-TI~ol&n1kxC*`q;4*aDKhEyg44dYGxX>6|2pUkYhv<CKBH>RVsJSPBZ5+!W}0+Mh=K1R0>Ha70tp%$TjXVpXU<_&vHkenq%E)eLfj?GFDy;!3W%0Ei^)lz;R8HJ34u>JSdb1GRV3l1~H&7W1BV)tJgfhVOxm>42*%%ITm(9xMzuZ`V{#2t0G8?0)+*ZwQ)--q&HsIqyv<V$!4a!7zLK5oAwLH;e3ILym3cDDa@w&UlWf1SPBE>W|nPVL<QG3C7=I(xOfy;KO<(v9~2Nd%3h49bg)d);A}>~|G%W`cH(no>SbM_P8+y&GPlPSgVHthy-MgI7f_UHs0sP!Eyzh$spY;1LQWxt`ZbZUUPcv1KxQoB{71=uIZqepw}7I(slV@GNNS3CUv?l~YFKljbXVfgMls<w%EFy%Zr5(UIMGD=&M%rR<Sj<_%nSTX56tzJ2>qfA?*OLG8c1>FD;_-*da0Bm3Jg(&JU=Xh-||H$LP_urmZq7gb`52>>#Su=Lf@&QyV}zc33G-)IoRT(vOgvYdDO9^%oBcBh5>f*94^-upebbSoP5+55XPj}nrlRbEU5s}`$b!JJ;Zv?_=|K>RqN8VW3x2WROV$i0wi6VO>PT{RYlowKjKGnfzMD)<seReJGk75CFpc1~6SaY!%cYB+gHjFM1FGu20#m&ANiQ21;JN>x53Dw%~ER^$O3B=$p!g6@j;r#NRG==?nu?}$r@2?e~7@NNV=E|{>@{5?N`MRq~`>_6WBkN^9KV=Ddn$N%R~&JfZu1JF<IsF&Ol_~?tfy|)|jilZs8+OjoUpyT^?>Q`1wOV!s>CSc}@PyiBR@EkOa@myL~u}%H*;+mCO(S>8_79ONQVN+o&Ongz4`2RSV2fhIh;?`J0&dw#VlPJ14T7C?lFr8R>G9*tr?FVLl#|R`ksTcX_1Zb7;f)yAt<AYrOWQ}%5Mgtdw2)s)K_lo(y5xI)@sxAP@l)IBBAV{oK2v+(E$;dcnGN>a&&H<Z-U(mA3>c|>amjbJ^o-Sp_F|jd^%()3Z)h)0if1UjwBnx)_)BEV{!|TqgTNkp)lhqfXvX@d95!25_zy`c)_KIt}%xTSnl`#_Tq)B01b^v5$ODX}7&XeR|OT^sfMn#b+E-c)Oj%>xj&~e4C09_BG6DxH?7U})2>bl1ye@s;>j=!K6L=8+#opa-k(2dZxD}t?{Hy4dqF>Knd+QVaSPL-PZSIg0aY%g6u@J+XKbUE^EGX20A21e0jgLBAYx<9Xyix0b`iM^RPO&3?lV&K-j-usURdLG_-*!^t}NHV^E_Gw~e!p5G@^2`c1swH{2q`8Qh+eV=|IkRls`Vm?jh2601ZhJ_Gum!7dE+VE!5&ABz<LdsJ^6pFe8=V)Hql;@rN5TznZ3ZV$xr7$w26oErq9vz$_H({)on3O_67yDItA<)msPw!9(%Tu);ItDC7@qaFc_Bg3Po;yopgJe{MaU@P1;HW*);XYMQ+?khc=9oP=^<U&v6Kg%6M)m?u$6qSFH~$ts=`AYrhn6>Fc-szGag}TqC!()pLSXz6dm%Py28n&uwmBKv-}B}zL6Qzt$O88-l&%ogFYPS>;LZ7-R>`L-RbGR1I?)$26brZh(WoXD*|<U-%c{S8zXt7>jvu7&+a+HPB`a8Ntn->i9;1zF?I)$X&tdrYn*+2zD*atrk@t*M&;=q8Vf~GshzyJ;IY;Rl`jo#+iuL5g`T#pln<!vj#WsaC`n<dlz&y8WBK6)VbjsSc_Q?`?|Z)Oxj*m&4ev_VjVm%hUVGiYIlNA7K_(Mp@GYe;ribApIJT|QQxa;(ICDoOkony5a0RKkkV-s<ziiM4;bkuM{cSo$4|{$fz+B2~BBxGj`XnKfbBpEa;`iORY5jkIj{cBf=*0ge=Zjq^=P^wqI&Y;1;r>o|HwjwZMx&^F6Hcgp8jat4xdbyaXV<fRSX^pt&MsNW9Hvr93e4r=UX^mR63=Ntv8S|U1mn5ri<F8%!Ij;oD)5|cMJclbZySlkB!RTD9xA}w3g68rayQa-iXh85nA3sBIEa`Dc!ugZ8=f^d_75#t!^7rK$STI*&ODJXM*&N*JY#Us#QX}>rchqqlgX)~x4fLEC2P}X!Z&H=pSKYsZL9rK8-Z%#zS^6O#29Z7NMnDil=mWLVSdDXeW(I4=~ORQl9$VYR8$zdRgBWO<iHx6tI#oTMu=I+nUfeGO$81;bVkeUAdJHwU!>oyBKw`v+AgdiTUPcpQX3LBjzno3cyVZzdT29(E0F)^QZzIiv*<iDJPXUznr=iJ4gPo$L9$lKEyIq;VcOkCWyHxK@mAa4NrhjMJkfTG{+~F&Qo}Y{2+?y(V+a<*VQfWmLxm==eEF~njS5-@Iiocl%1WD3;kgkH!b5U#618mEuTa{vgYfvNWR4YF?jZFWujiAYaoRrd-l|t<zkG^gF*Al5XLXXp&T1*2m((w(mq(&GT*LaXntvSl2n=uv%#gK=s&TrRTaLzR@wH!^u&mqh5{~F8;AEXTfUP4C<F{vNf#gqsY^H5yew4&PD>`pH9npN~=?L!6@+%Ulj3+@Hx`{FB2ev~xv>+}aT1@P~!k8WZ(;(+O>i@Ev_^4(b51WYvy6sU3|2?J(?9UnXsjcD>tqzm(I(`B-$KBYGhC&;;r<Zf)rk@4LXKs2McVXiMLp7exLc;bfHW@9S2dnT*PGytP(sV#F>!Y&Ha<ta&u907EGSt~6T2)$JV`9qi%{3pbHNIt~HdQQU=GI+Ddoo?>NwJsEb!&a7bTDfo7nWZI2Z=h_yawmI!lb~cvpXC@;DfqsWdu6d;+*ywtuG(lsJ=T*CO+odD)zL^@J$g_Z{svdAhl)Byh`rU#Us%|>Q>mI0t*q=YKEkRCTdXWaxP@dKEDpq>Py>wBjZmXAeY+MTr0mwsL?3b0QVB=Lmf;W7Kn3tP(%mQyH2cw1Of<9E(+rHL2EFe`LmVULCy=7XY7JLf}u+J5J?L}6KDVu?IE1i+F2wL3;BT<T*c8$OI4f%gM=wM+!*J~n6bP{10%*HJJpIe6tn+QE&=mz%`oV@1P#qtN)AlZa1(l;!`Q)Oxit|@^WZt0@~(;QLls|^XJ43ppL=jkc#;-HUN<6HBXWqUdc$Fohpb{8B}j^>k1etd?Ft=Ay~focCw(%Si`Oti_@Sf3!{7kj9g@ODb797IjL@19IMBiwb7FA*v0;;hn(R2qa5UiW`+K?{_TB#h;zHqx8A1>c2?TA1pWYgm^`&bu&-xGDh4I>tn<zSu!V|io_6USa<FF+Mxm4elUZcqjNu+Xj(2P%}8Q3#CP;}GB&Gn$xo6cm_L71drl&Oj%mKY3i+)E$AK63?FB&H^|U3el>C4s9tz2zjV46N9qZrKgVgU&sNYI2Hp(%f0GQJipCf&ZL^Zc%<OWuBmL&_tHx&T7c(o2$+XOIr9093am)(-<lL&WetJh+8CUp`LKzm5>GT+N0k|=H%SiYla_63?Uaywon{Et6K<Hz~VA>XU@D<fo)lRQHVgFGM2ORNwWPWL0^*a7+i|Px{Yr5p!v+uShJlAr%*W2w}-~NgLIF$+xb#1B$Ff-RE~|HJvH!88Pii2zG0u7WWx}Tn3@Ns53FH{DhJ(8rh(-BbOm>o&55Kj@d6kObrGlZKFD1h$~M_2U1_R%)iPdVZC+Dl+Hil-O4$XCu{VmuJp!zSQ7L4``<E!?=X9n_LUjnh3>%SDlO2+7Ir&LShD(>m-X!S+PdDf278)aq=e|8>X{->sC>W6#o}gmc9T+BsS%lL~Hihs#t+Avct=Sret1wH$>?&D>5#(sDOsU|GR?jj^1iFuJ2uiDjF6DH0nUGpdTQ2}(`I0=x1v?n7uK8q;dUo79p?_BLxw*JW<CEww?M9Fb$)K%W+~><l|4PM$QXz~zV2%lj9thaX8{y8u!BQ@AlzY4FQz?_zsU+=9B1TX;2*OvG@qYQ)4Ch$nLc6(9*+Oiacdt~45|cBAy-?~;464N(stXmKlowW1aGSQ%`Tj&UbUjiU0w=080=w#P8EZGQsYV~e{dHlD6Y!+%3Z<8jwh48oHIcAck~Yi86A?rqg5_5v0oXZ&5a#V97B%BOIGQ6hyD~V&`l%7<O<5$xu0*oZPPm}ft&$j4Q9ZDKB#K8k??fzv0(R^fSjr^I^M?rU%&$qwQnp4i{|fmpmU=nanH-hDx9|4e@4bEN+rGPx?ho|z^fy-sA8Fl!Qn*<k6~!=gy%RZj8%C36F;Do{Svf4)TUDGTszjHLZu0kc2oK)w`9Wo#k=RL)>E69Z_j?Dv`+=Z~^v9y%YUyC9yu1s|<7gB*F>7QB&^5G1w3J?y0kqLFYtrDGmwM2^jJ8oTv15i(YAdX=(@?N+ei~SFyc>|3=u~I7%q57IrOdGMzC>1Rl6P`B72BcqbVJ1{1ujLAH5vuv$yJYpmzHOfP~zfH=U=EO>JqBMSzK&Fb#cE=oigiHle19k9-C-^Ype=SkYVwG$7tk7q#fY&-J)S60t7y=<uzEFO%2M?Q8T|uYh&!>p@d2%>U5uhr$<!9+zz*EVUZRCWxf+ZGd9O{Dg&Ga47ws3gv$72x~w!0LN`nT4c(Sk%d-2lNdOU<ai}D>0<z(j$BQ8@X07C=WRDRwDmCVkGEt;d7>&~9ROu<$S!AH2(c_e~yeiPsvQ>e0r|j{R4yHu6BE!YO7~ZD;VFBVET+`ugVv0n;RAS4B$C@cvg(2IdO^|jQkqi-zSr?5NjOEIaXd8728c#sPAEaG5h3->yfyV1alJo1ma}S<1mWxr|SEYkl89<B5O+u*jIkBuFV`R;Za#d(HD-QZ*YE4m13Ur~7nKQGZeSnsS?*bAN^DU=dMOk^?I!Yl;GQKCq_J+zm6B6Q}DAQz%^^hx*&_(fB&r-8j9S&_35=e=y`ncg3yZgrK5)={5M|8H@JEG^%81dz^6Th6~rXrWS-sU{i_pFx^@fcS&wJ$t`i18Vz^wh#LGg^?0VlqG)X@xBj6&L9QxdKK=n28Ap1~uFrmrGAX9fKa(V<TFYW)9tMau31gVK`bsMo5Q^Ovdm5E0>pZgvX&C2`ysU$=8D4+%;E(^O*&ph{IM`z%|G|@k}1DRNHDZ{D;=Wt2Uvk;%XqgNT47gOXZ2e0K|k!Bx$1Bgd+In1w_*V;~@2yI&^ooOs=ZTurWWR2IID!k9NkG+%%R~QC_(+FoZ#FO&beETlG~cCgnP_$4ZUlPHV^Yw-Mh)sKwUhoz@=}>_Q|%4w1y4^YTUECnysJd)lBrjI&8FeqJE(9N!cUm$clBP)qHHx(U0THCdp=C(c&O#N1W7JQN1qFCew(;$$Qv@NfkCk@yRs$pyD%71h`%o{E{88BUvyT_UzlCx%}T(~f&d66UAi{X9hWyUPMA$++ntgjb1_(a~e$ZG}xwz5<+wnil#b$o13FHY5biO}D)jRV4)e@lp6L<wmtAmdeWV(bh;n6hQZ(SM(}S^ATes(UI+rM0ijSo#|vVbqcF%1bDC}W5wE91_BY4q(<2X&*>7|+8iz7d;LUzZP6bBMJi>juOe05%P3a0;-l>V%%L&|6NgYF@k>Mu)>m=8NqE?rrVD^aQmma=4~r9*R7pt`ieT}yS9Hk8+{gm8F&(87*i3002xu2rB0|$q<=w}+Ym^qArPV<e4zY4(7a>P43@hJr&=p@=6E`~R$qDlij?ipR_psEZX+WFMK`om}0Yk~3B_fKsLx(KyxIx_Uw&9sJ=6A~R*T{RjF@8C5xlY_ew}ok_pmX4j_2(+b3e$S3>I%WReU0{Ne;=HONe=8@bU#EL!<sB86IVv){(*4PHnB1oJu#5bg(%WKajAD)VpbG}Wuw6~cJ)AX|9td;3T&-q<tqQ^6pI3jyc=?gG(O6WHZT%*)yRmMAA?n`I9lBuaV!CisNgFpo@p+wl?R^?%#o`Fp3Xan9eMJC4z$iu&$cOTZOQK8xN}ytCTc_$w?mwZFo*E%sfe|opo>O)g1CrH994QprC(i6QpG8h0z_-D?%_#u=m4aOJ!j~cNj@l6vyQ3aTr<iw#V%vj&8XQ)1lOe2;6(}_Ko&@fW8evuoe=g-(jkZxu36T2y<8p(irU}do^ZCfHsQ;RH;L8~#ch+cc2JIZ9utG0BXF4s6tvJh1ra|$<`0&dGUiRSGF)9_xkXr>tvt<M!n>)Fk&Zy1Ti$?c=Hm&H>ENbC%aMe`6-n1ji*Q7doH&^^=AICG2dhrynNfjt5$Hy!v2VtFHD#q1n$RmP9`T}+EX9_!=UlEUBqU45eMvQl_xkSi+`ZK^@OAI)=E}p`hArp~U0%0+N%vu}M|ewui)^s7wX@dnd;a&sfgft$q4glD2qog|9)U#3H{E6xl1L4i&lww#;3nigYwccPN%#sqQ%}d?tM_`@n99)I)c$--9mK8S%I|;w`4yB_0(wXa!GscNDTC~u5>7e0$8W$A23|>zio?>kgtKWj{CXKmyZuFQg7735KxMit@Q<kV2+Rk5ux-P)P11?Ev~!XaKOiL==Ciyk3jlH)J~D9PWB=D<^nLQ0F<!(_a}!V~t}&bDA;G0^WKZCcxG7f0yz)}~S=HoAb2|Xq7RqalA+fXoF&*ejrA;YwXe`i0Lu9F__~U}<SvnqL|K7?VNpw6$*C$Fm1651G{$P@zX^#|fYnVgPmWdxDI1~W_J|fMOdqkyiODn#T#?lzqvWlS!`7q0X?Bi%mzbX};H~2W(K;twHjtI7;^_V9Kw_c;i4hcr2XuQtXJt(h+%F*XqEqG>m09*qu<Zz30d}6(wcEa?{)COO`tMGu1<2;D-E_;Vul<H1X3|7b0tbmITVby1j@4k=^z=^q{dh+@#b$E5-BDOwbZqAs~Ywj+1ZbLJoPs*{>ISoyM#%mX@Jmj%b`==Qow0X(#3(_`LNKL5XZ9bP$$%G1Xtyoqciq_Ch<6K7?&O(V;ap~7iR1;%x{Sb$0CYv}-x=h|gIXc2>2_PEy?W6_;71$nkR`DruI3tpE*DZN{b?$qdy5woaEqx3iI1<%ZihauAoj140#i3u|%h7^43O%22QWrg+coU(v!>$k^k&0p1C9ao`%CdvaZo|Oc#x<OR_%HEAIM);Boq|4T)<J)Cye>~zhv?8)l>;HY%0{rsy4>zKarIgzC2Bm|Q(fhzNkmlfv{=k^iB+zN*ydI*x$<eLaL86};#=BcwKf9<LVQv5gJy1tMpXNKwf`EFRb00SHf8<pVfyRvs51PAvY5gs@c|zv+diCy9kV#BS3#r&{*oLggay)MX>h*BMm%V*hJ@<SBY>3LYl3EU#;}!xK@m}8pl{0oQ3kIs%hagyrQybzA5q~n$wDymX7}_p$&K3CZQXDJiDY%Ihtj*+dJ1hGAAGD!F==eBl7y|ZLh<i*%r#1^%|4fi64Xc|aJx&QVAf4_CuT0G6bEe-!HiTyu_Fk95c;p=X1a_3m`Mjt3DXRuR2to;+loBMfsJMkPE4w55HEqDald*Jl&!N!unDY{vg35_nBe%#WfGhdTJO)Z(kEB+wj2=G1ZK&A@NxDV)k`*lQm3+cAfN0JNuorJVm2rqouzDAyd5tg90oqfK7-AkiKCd7wN98f!&n$D<q}ZNll0Amp_z7QW4vB#NB2v}H4$)aS{jtDS=@-y`dX<qNrsF7WzOPn_{X&mxoCva1>DN1fVoJU>Q@10_cA)>*7~S5I0091aZBV_ajRG`a;YDirVfgCMlgVAh>G)-@^IFab8GB8HHWg$+OfM<v#Y`ch;24w#9{fi<VMZ41yq6He@J?Nm<ni9=p{Cj%dSZRPRWZR=#1C_bk=)5sd?bA3-gCaxe3kttmcjY#GJxjYaCPAw#!M6Y}F8pON0sYu$Kw#=A~*z_<4^&D^j(3(FzE~E(R9a!!o7D7A!jO46@kti3Jx27mg4auKL7F9RK49>Ai_UP8!%>u_+Xovj3&>?wA{%@|bpmhavcojXlMerR?P8Buwm5u4M@$xS|y&8IQ5Bti1bJdr(*i7-sI7gw?nzNRg#~ug;lV1SN44g69pZ55VAAgHZKrk7Tj9`)k(vh*qD{>CkKh-!{T5SS@9Y#Wl7H1kFOyjZ?F;<_qPWlKIe>RPGsl!Yaltordn)?z@kA9^UHjdDzq4fBWlOce=lG)6qFKb=1;HLsvDOTL;y=V^Jf7Gj8psRX*V2*T>Er#8CLOaG+LphmfPW6k#trbYZQ$l(;P-j%~)!2CY0eJn@*^w2B>ype^xKGjP<ROMK`nWxX6SPI7E&2MeF^vQ}#pzYG`bI&kXA3pKW+5+V$bo8e7d`6mbFg2&jLkO0~?dO$1}9uL&?U`Yj+O+Wk)pb6wW!Sv;}+Lw&kHMKd}b^=|Tcv6&dG3m6FCosfrW*B68stq1tzBGO_W|s`V$4Wmzw;}*TeL0rXcyKv~I`-);4Q;r53LI2ZJG=t9imO6H_HJ3?VgXUvw&qb+F`aKCVV}$Dk?^-xv2X0a_aY0~SKQT5Rbnz!$|R8N2DdzJtrbC^X?4b-V512@1Iqr(Dm*7S)Zoi#rS`>nmY&%@?lNGsqm6v>f<%kIBX*=_{7uw+%J<Tk@VB9sA0m=pNm)T8`b^JbEu|!>eohCA21v(K!kZC#4Y%G|G;FH*i;siig&vE?i<pn;Txg7!95!Tkic{j%xd%G|8;}KbnZ81s9S_|G4nljKc}7o&n9&KQ|FRg7CQ{UPIyXSNH%I^$&(*sDa#k|q5P>}Ps>4y_{nc-rRzoPxSB(ilrSSbxjUgL3xMpKRpzU!1%QAQl=bTf4RVZfo%-U)|Q4F4mGO(Waz1KU?bMI)X6irb3@7(Hn&`X#4{&z?H=<u|=f1sB-9&mnoyT9j7ugkLsJ$(=E_BcQ5z4ySi&oBFlDfiv0V<vw-rE>2Am!Q>YJ{;)&!tK2;yYKZ}p82=B$(4;f+v%T7b&44utFF-={!Le)!sGu=vf1QQV{GW}o}fsv#>gV1?cg$dgrF`S$G2>7LV*cmXVy4ehJEzKAS_892nVN70oIJo_54-FhM4>PDVu9S+RU%QVbV8at$Il~6kQ!rNZ};5s}P}$)`sMABq{?k3$KZdvg=_E(a*jak{6W^sZ-$lDurt~(?)BbcR6*{+^-YXeo9<fVZ<cvc9=j-LXrRua)S4f{)ObF{e46jumfppLvgv{_E0iO*6vln1CI&gsMyY=(l4CF*s@lRPLPZ!fjsmNW2eOpa=Ux>kqHc`HTd(Hku9v!*b-rTS_G8~z~hM6DT$QX*Yy2rz&i<Ggh-Pu?wQMlw~x#QD}MM+u}kI)BhD_V+Wnc6kh2RfhqA02&xS}e6JH;#vf)9uxLlw(u4_f2JDsRy!eI##N3mQ79{8=y?n!{JI+%t^OO7?eulHJnK7C()+0%dPZqLAgdu)?a(^jC5TL-p_!l9Q)nVOp8^fySGZY{f1_Ni+c*|kQds$TB-f|@8osIGLu8ywI+x0}ykNME09qb<cx%P&DhN5X_e#nC73G4noavOvcZnSc-~J?YbBWqfI=iV94WpV3Bkjaye<!a*SU)bKyCcGe_&6$*1F=ArCk3p)1C9~AKykUW_nIted(K5U}Is<)B2q;F<mrS-e{f<4i4bc6(ANiw9uRltRu(}ce`l1rd>n>Oi(@-%Nw1qIL}amO}UZ{ul(pzi0ODi4&8&juaA70fafa3z?k0Zq9=DV5xV9gmron8(eXbs8>CJ%J|Tb8JmS*6X-W+Y$~v@b^z)p607a`7yL~g1&^biD$PfNMd+I%!z#{P7IRleFKEiIv3hIS`a(MSKUJ?m>|yN321O|SCiKMLY-GE=eKGa4aF}D48*V{Klkfp(bWrtqMeolr%6I?+RPONDCu9;R!VdhpA4P?7g>We@Oi-z4Y&vsYy7Dk^-6Au)^brE0XoMQQK<8^I35=f2b3wXn(MLcGa;Q<3Xz5+-Qbx!Oq^0cZYHgM)!+A*fv;Tv0FlUkxD~j`xxIJ4b9)mON9SikqAw61oX_+h_TBF7zI*!V-$rQH1<t<pO?;ynwy^c*gN;rkxxqj6U`F}&kkK=-juO`4G*dzLKjH8yZDM-z!WQAoi8yThzI1D1o6Fg=lX3bcNxCRUm({{D?BXxyjO`U7)btNH=tU=)8GxgSTTFR*PqHg1?@RizML^(oT5L$*-LdvoiHoc7D$JE64G<Q|zUJhSzzLFKp&B!m37W&tT9#{_4yV0!&+^2%t>P58JJ)rG5-;`??0j;#yatuO>C32RJ{EL2P>Ovkp>k_=(_AivJ*LDVLav$5{iDXo5N?+?IEpVS-<U`rt?rWJ?Xyo#WKVhFYy<xW0@6!kTx<zOky2)bM$jT`cDmR0xmXOT%n<l)+{Y=@<~0n<t<xi*vd7vV2NLWX16QFWZiCVG9m440ec*W3(L+96D@dGNDfim&!PSHvM}t;$zE#XK(9?adl9sp`;HkE21?@P#U4c3ryp}On(podZ%5E2^Q<IR}N*(HO(ZG=8CqTHbz!2aW&TuRk+jh4z!jt9E$KuQ-s&){7?2a)pWQ6?U!NG1@9(AzAPMC`tyu@PSc?*lg@HQgGp6(e>31ax9*{Pt4kYX{Eh=EqpHj_vTB%z8y9Q8t&E|{5IZsQ=mC0Q2@Luy-9Fi3em49DS6zRi~IYwbFXSVJ!un{6NkG8Z{&l#tI#DKaV6Lkn6V)Emaau=rl;46l`~WGI1u(;2n@Z7i;_i}ybKL6GlrTrgz=Fj3h(d-Mb#Q71?|w0H8yppv%6m17Y5#7le#f3f8>K@?UdWK8%aY~>hRP3?jZxPZy$^)hJGWJqR>S+LaynQIgCY>`Q98KL#IihU-rWevWdZSleGLu;`<C_Y^OIPjmweVa4WTI-K3|Lc0|NN63re`L|Ysavesr^X?5sqgEK4QHb_;<?5&3vW=;tv0Q!3a~4;XWdvjK>fU@<6P(Wkj5cs<gG%HqZ!I;pZ@2g?z^tSV>4y_o!)+Z-ke{Bq5Qs!2z;mS_QQ)5$lqWI-ej5sJ-5GhdqVQwrCESC*k<0zvz+|-AQIR4+g!RBlZZ587A)s;VtHa8Q*iy`?0-5vAo4aML@Cjl6y<i<Y&nVzF_lD-BxIBL6htl;&f*3A_BK5Vh$LVR4@rB_=-epMR?a>?7Ym6tFz93+SR7*Kgae?LAz%`CEy;9sh#@=-pvxtu+1hB_Pn|7r&t%o)l(=Y$)UUlC*tHA`wiG1!NPd(YaV;*4%MG`saGHK%M)D5;({4tr!{=PrU4q94&6jW>C2%V_w8S?O68T(;R;<PKak_TZr9t{&jvY#Hh}gVDkX3#U+J3GgB8ea;-j7gB4$ij-5S(tjJt*<m^!S-O&cpm6Syq-uNi2oD#eb^Y6Gly1rQ7O2nxJW8m&EXCtPWR&WZP#o-3!SHI7&&K92%L2wV#itJorR;w@(dPzV0FJe*ddmUp;t4m%q=wF6PmOj<7{HbHy!=uUB!4M+JvTB7`YJ0v&y$F7+@spOvF4Tpfa~CgJpzfBpTRuIO@@QRFL-;uk7Bg>(@^t19ta^doe>rJ4yy#$f_A%4he?p^U^lB5wutkQjkT&6Ou4ZHqW?i_e={kEkhRQnMpX0chk$RD(nfD5R@l;a+*Su6+N+Ba%P|+JCqrlVd_1!9XHNf<#}ycq=ou>rRwk44uqd?Z^kH7s&;K_>1~4G2U6b^8Leso(GlY@J)_G7gDKrRWaG*qgUFc8WmkbG)c@~`TlnIgCBUjdAQYbMGs`8SSwVA!Kefno6sOGa9$^Z(`h7Xpp-c|O7Q212OO_CflFivXH+0Di3svQMw?;7f5@Rw^D0(AtYUal0u=y9rZ&{5*Y<L|($(HxS(Wsbb{#kvmVDia5T@0RWYzv_`C3iR%LzM_)k+T&s*nl8hkPzonQDigDrndY@V1;8YFC|Dvj|uTD&h~q?IHPG@77^LqLk<e&?t1mJEn>@hLePM)PTJ#*HAi)<}7q7_EhB}$7I0+jyar_O|52IS<Z5F&4Lj~*si}GF*9<$Kcq-CV{>gp6Zy$OPG<s4JhuW{#zL{yi;lBP$aBIsbYV{8Ij3`l@_N?8FyC`C7C=dL?>2Sbm`P7%w;?HUit5v&w3C1_$8sVqhuuo-E}~wzwucnQW%(+mkz9UXGU-VM5TbkLcHW2-S+<C^$zfI-gVyk1n~mip$Le`R<LWz(p`#4w5mu%zhU;?>9z49(?jV5cC+%k$3tKbb8_mai<7|dokA46UZuNcJ)8F5Fr{|&T_>O|3D_3Ydzi{}i{--~`Syb*RzzX9yT}H&+9I!zL^zWX4lzPDp$rAk<7li|k?+cP%<~xZfgTs0JrD9T?2#{An>UZr=!M{wh237Qqr<S$!VDCNXA^D=ItiH5tGZ*pJG2%WVvBFt6+uEU(T7V}8^RY$vbMu{RYi&>!Cw=!35edln#B<n6ZW6l#qsu(I($RSZ$-#*N)3XR`Qhk%i?Z6Id2uEW1q_tr^=;?phcfW}#Luc+61+a({Tg-yJK6VQ85j&{_EeCWN@~tJcIZ24?%GE16qjO{fz{mTNM&A1J^?%#s1m+@!XAMPTrlSG|bz19uR42q+@EFrm=HSbJ9H4}nN)96%*<8weInH^N{3i;cb-uNrc)w`;!KDWz_2dDwa8k!V?)Bckr3ufq_PPh%|AmdZg_Yok?Z-*>UlOOGHT$-==P$>}_O(r0lI~qPsL1!qhkCUnL%_EpHKLNsDzn*4zOQ}3u006PIcAx#fqLc<5f>WMHHCbmB7n;=Y(tPWq5V{pb@tjIpk0>i`flhk!I24&RtPU3hKU_LE9p!~xaWIik6AlGP0evqnsFn%Tql7KEAMcFh%aAvl=5LAi3eK{^zoUag1&sIQOZZ#w<6^`%l9OvA+I+}_6XP$#d>@LfkwG?l76k74RdCS7QammhOL#yG-{ccHpL+2j5yvEmN@<!q29LGYrAJj&@vo{)5FHJh8!YN(&e`WdRm#PKyPoLUrZ;+V$A_PI-Z<AZl_i?lDm>$s+pKC-xVXhgu#`VY@%kv*i?CCL6Q<`M8st17~vh!ER`f~v_z;(A-RYoyuPiJpDRD!vPE&U(y5D5(>iGp`v}+#Pi`|2-%-8_^>z&YGRead_<BSv_ioA3o!)~>(y(z13wCWLEx)+twMOQDx?Q<RTST|>VnZ-z=^anq-WN|XhoBkM#PmP6%LnQ|qa?;G)pd4^#IH-rdN*uoy{@1i^L;z}jt;e97;q9uaQ-6yF%rMK1nn+BpOd(Mv*}oGp21MhOw_-5RMNlsmIZz4;_i1%bd_+8USBoRJ8I|^E{lH%!eHuvWLMFDo5P#s*$tgGIh2QE(&PkO2SlYiJfzZxt;v872l~7J;w}M(Q{`w7;rNpoGr3$zn>=p|&ZSIV!dle+Yb5z2xSS3XWdyx^Hc0f4`Q%iKa&&*+Ku@nb-uURVD{wFmJhx)wX0!lKw;AJ7zVlG>Y)`{fJHjO{#FHVmCxk|-Temi-FS_9u?{3&BM}}xSX~V?MPSUdlVmmJ>zoZVMY@{F#!W#0Z#r?b8i)2uJ?q`dug;?vO<&~+5?8HIm%dd>345Ws~n}o}dc8i_j>A!C#wKodw$I9%G5nN^VrXu@s68r7DkG{BN545SoUfZ-KiQT0GJ6=4vqPAcc`jZ)(bIa#QUHl*o#cRk+93p?0WIQQok^Rb_u22^ezErIqZtW0vJ}T8hGt2bC7>_Z#Un80P%J*Lq^!xgUD^f2~5+)iud24?dat|j=yn+l`z2Ely0JJF}0Jm9`xPdM0T@oKhHO;`&leiciCv+?CCIj1XI;E`$-RC4<Gy0a|s>aeX!6b7LrZ#Q($cL?+EQ$k?{JNA;T=Y+bPZ|!1qosVPcG8>x{D^>zO#=CZ@)-W}zQ^WL5DtC|vv$1~QJmM-@wUZorzv;*AX0bLK(G|7bGK?HW9LJ1T2S|#PlYZbKC}uMeX^kTlN^h}44_gafWcryW^F?=60Ri}<rpEHMklpt?J;6!9#6<49md6esJaedZL>-`%G1P>OXBF_q&2x#FPB1RJXe1L!ZVgHczXS}bB*isDHJ2v$JTt;O1C=MwH(*vGM)08s@CV3YLbYVmTjQ8;`(7U3Kubwh0M<80&$nCklAtM2@^PebfeuVHzQFtetPpvQ$^}2TfP^@#xe;U7e3kR*P2cCgY%f|N1yyV>tHr6e6lxhG?{E?$9oqm<oEa7?tj!I^jSzM{1G@=zcI@W8_DNVX2kGkp=610R;H;8QC<^V2jP8hqOWh_$j)UWQKJo|!wJ?W4b<zImtTmffw7R}keE?%SYuJUeQl$)u@J=Qy<aCg9r18Sl6bZ?qA-Rm3`y&1F=sA&r2ZpF7W71jr&sAMsb_*RL##Z4<WPvKCxfkxu;)J?^**@Q%>75ItI!ZF&#Vm52(75Z4p=b!rI8uQ90{m!+DfgF4A)9fzu=3$`*)hIRcuA&b370({53Ua=6B5PJY*6sHz1WJh-(9kP0gvXO>N2^4RQldD-kRwvKI*R)K-JBspckwHvk!(4H%>AjUYxx6NqvD(cQalAmdK=cXxZg?74Nj=l^f-%6i(!vhZJt^5U1Yluq~b{Dpa*_fd-u?rzis(vU@?C=w2Mw=rfjV5cz&ixa>$gn$>o|7FCjDnHF%nDd=;tMF1@fvD3ODeA^{Ew^snbI<;L<KsV$kNnih!)QCs)xFS1b#^aY&UUf^hr4QT0g*^Dky1PE-i3I+k~Rbguze1q?wN`@N}yB$(6ME1>ke468aLO9?<s%SSi4l0`T9zRRv24cGiEqwtZkYf5MZUVU}@IY(d3%G1mDI^S&{)pCgh9^Zh{JdVc_a~!+{bb7hQN!Jh=G*jB;HMFQ=nrJd_0b9Sb}IqwzXE&!TuB6V*6Yy&Mqz$m~i<AtetoB4fi-v#BH&CiznWlPTVjbpf~rT`05r259YqkS1|(z5<Q=yGL-BR6HWxP}eZ?p#ZFRiB=Ymc*lqeACGt>;>w^L=3!@FC1iU(8_pecY~85@vJ2`kLwwsde}<z<;>JjV)+$`q->n%(LBN#4$wb?{%$4+{Fwz+Rtio~UY2lbkL0$HYhk#~3JTM=Lx-*&`KEPq8_n<;7dv>p7me9H%3P_e(gG?=b1ZEifHNvbT94+`#e7<bF2O>V8vLbWNDtBHdlB=1Jq#-=@kDxEZf?^NDBX=bC)`2^e$wh&W-4xQzlR*c5VOcuCZ6^)10M~rY<fu6P;K8i@4r4%Lu~DgkH9)?cP-@sc{usF+@6!wei6H3UfH<iMNXTr$BP=U)gs0(<0a3Pq@K!1{rvl0~**vtAv~+aXQj;TdVQ{Q1-kWrh&oF6%jyZ=Oev>?ru@pyXMAeTF13kw|%}6AyTCp*gpcy#jcqV+kBRA^x%{l~n2F_jWS{KFNsQjOd{NiGgv{b7cS-uT(Zr6y$Nds_&bXe12?*;0?dGXZc%lfk4INHA7db!sR`XAHFk?CK1jmh*KS_uH}qW1LkSmK^eOc<f`g;^od6PXhbPZbZ{Xk<@EQ2)_=V40|~8Z=}18{KGhZ2Ix@>1mgWoaUQV=QzPTFFcf1K4;}CH@Y$NsJ8nSEl^8n69x`-^ky&mmw!L$dLt5E;LUDlth3~eZZtMJ-u;o#j~L!lp))a=+HclplIbgwYO(s@NWkQq{}ai!ags8ZPSqi8x;_$btFR(jGgKc5`vBJ`qf3QNp{uh0|5ANRQjNQ2x2%iZFCgCL<%Lm5n+vn*Xy$Ik+lZcDl@|b}nn<c-U}*8a{qT~zpx&~O_7er@Aegr%l>LmsT@ZT+VLun{EO-M5U0=OR?t<1^b@p>{7kO$>U<>4Z3?BO#?FOmH!s4zJ2aD=__vk_M$DUCg?LXdCVCVPeBNNYhMRnw$p+Y)sr#kVR{2y24ESw!i%~Kag?jfBf3NJoK<!MnKOFbWn+duw!546d_ibvN4mOrVtK@@CW&fR<T!##EE6RON2?B1oIdS8^l4!3WS4+<~Yi0+c-szMtAAkN&&dVH@K(`EwIjc|Qe%K`<d5<AQj2vkpQ%VFVXxN-sbb4YAK5tBzEyFQzfC)N09I81;Z`-tnb$76VaUrk6xrqd2?3xhqFST$}T$o$rg>>1wCd{z4HXlj7zJ-bKKhdDwb;UbIl@cg2Vj!Bo^ML>Wj&7-Pa{Sh+L1v9+{;F!R=5UqiUu26;JAHm-OV@VG}eyx??($E=Ml-9b3aDW!y7R71IJvWlc>rlw`H{Id<_!%{n1?`EYl8zd(qb|#ZAyUzCg?C>FsLF1yqR&XggM>a3G7O<8Sno1bD&W@v75TWmN()7^Co-i1^4t<8NS{b0rh^IDckQRVbJtJ`_;zDHvwA34tj(pNjEtvdc8!_r7a%>9WHgcu+|4y0`=LA}&X!TzNPeUz=zuRqdMKL|Z>+@x3D|9BL9efE{E;$_x;0{S18;aaIrSU8v#H;_?HMTk?eXNO*Zr3#UhgwEn~Z-P_l``pn=`Dq+zbW&;peF_@5Jb|`;Tl3+yu~~^SjyJGXs$?KYvr+r;}69{tVN1>yAUWS#eBS)&-n;W%AyVpNx29?&cEuo5C_30B|VU>}FEKK%8}c1CAAGD<Xlp;BMqUjL%V(2&t0~$iLKrMsyR^lcmUT_wVqY9oyJee;g$Y1D!ZjQY!&uJ(3Y&vbm}(n(2}e2Ef*EgXkoz&OET<C0nX~!71kT9DRgBPU=6dN+(FIM8l1ww*w8qeN8uX3pq*=1K>^vV`W_k)zMfjwOA{&l9eYFsr-Wj&2<zZXB@sAtFk}bbvsF*<E4_(nE>am${mr%kHr@A8_|RMoA+df(j$vidTo3UHHtpGCI^#3a^xE7(Q#}3Lax-~U&o&I%#Y)k;d0|GXF7h=;;LHNg0%sUqN*Zksp9C+D0i8cS~bx8CZaHAEBlhC7Buo#)82`($*I>;adKUHD{c+BMk<}w%t4tM<tKwb%>|uOI0Bnh`NJwyHP9N#W@`xC49+Mu>fdJ{Ibh~tSorF6qLAH!`uaA!tJSx13Ul`|>|=RTMY8poO-W`B=QC-@KOqVGN<1f-D?r#WlDm{rf$M&L5nzCfPfq8wxkVe2OZFK4cVNWZ-uEzLecYNs*8<I@o&4SG%iVG6Z2Lm0a9%A<`n~V(IkfcG^SiZwolqw)N%|(2J_?5$dcRAdUiGwgZ=Q5%dYG*ZD};Vv<U!fYF%<ejC)dfVjMh+jhIBb_sbm%eIdBlTiAaIoinSGEDE+oXGTl^N`mz0%PwAj$*GJ$p#qSx^y>SG%rCH6T$hI5e1PLh})KZ44uhc7@e70kSD=40cys;~BuT#i!jXO;qw^mW|hQ;PhciQm>H@S9wt!5nihP2$L$J&j6mm_1YR??{Vr{^x;x?yB>GPGFJJn_0=Z-e&YR(+f68G_92Eqo<2)Y<3ZdHZ7Ci`#QI_zN09?<{#$t(lokc3IGuW)w?SErWVi8_<h0AdA+*#Sr<9v99L2vz0@okQ9FcWwH68Vy<6kWu7e6kIr>8iMKn4I|pICp^0<c-*aOQ<kLHK@y;sF-lGHArQvS>LRy8;v#Sdq@MT-QLtpprhD!(7IfkI)I$qTM%SX~X((G*Ii|S%!;G6bxo~*MR+3)pKj*T`DJjs3x|EcJ+-uux^BdBof$eFdORT#WAv8Mxt(6j9s!G~Hcn&A-0L<F}s5i*v+mTa!X$Y>hQxp3XV8Y(?$i821vhUAivj^lI^rebwXCEgpw<stG`yhC<;axqFv^YzrR<%{sm4}??<u=(*_giU!Nz@n(_OQ*hWasLbWIzNw$jX$5FcQZNa9mhKD;P12@=j!w5qdNLLZf85ahMPO+ey@H&$JY9WySpRwEvi~Ea$5q>11r7ZG!2_wJ*cm3O40$i+L;^>)q>Z}hoI{&oS<Q^6b6+8{+kgz9oW_h2Cm;hGrbVD3oHm3=C7XqI{9q!HFiw@o)93BY?ynC#v*{Q`HBodw=gf=OVUAsOLM10J(ZVwT+geK(a|aI^faSvgqP%*bc2IkgeqMZpk?jl8a3XGi+>sJv$`&Kh2~+b3Q3B<?k@tv0*D#g@m2>#9@*UUkw9FPqYTrrA;jqdcLBgW+AcBe>*{Dm1^gNw&beH-8drAWG|?clDUmw{2zH%I0+U@vs;B=mvrGRxfcDrv0dhrQrJD<ZroBQ{DzIhq(oPdUI&eHLQzFIik!t%=(Mmtj-K<ms{8i*oogE{ka2isvRU5)y;!0^5vvZd8aw57!nv&KN^Ii{-O)+BoMufJt^(J(F*z!zd-s}J{LKSU9XwCal6i9=h*h%M}3T<PlkuP36QRPp_n$X^vIY2MPa_*`!F9oSW!)?sxn1<W&Ddq))>#j2^EWx}IX_2kxR61?GDGThLv2#v_P%AmM-KHh-%4fFP#W%CL-A81%IH>Z9fb(9JW;u!a(U{+Xidz2Mb&N|pcQQulVSxNsw^RZGV#UK|u4YzBU5CR(?Kf<1dpRYhZHqR&kHuwU@yI5`1om;+{r-C%di3xiKo+Yzv{(K2Jd6O(uFp6E0H|O<8O*8ExIJoHIQ345zsVBgxN_9tjYrd4B*K_FCuGsL?4k@*xgqegv@am|(zvaP4&Wf%j7fV^CMR@nxbCh`1>$IW=dLFkb|GoZtU%SQUywD<yy;oB7^SnI9vH25!wAP+_h@}*dxLJD58c4PVWY-5kb5KGb|8VfgR9zyI!SLPNBch0fHwkH|EtvqdHm}L??%l)hNANUl=0-Lw!P76h1>AZnS%wE|F?g028qCZHdueRh6Zx}gU7k0{5y0E?Nsts@AtBE(2+FV%gB*~hO%(lPIb(i@G>ljg}n}qP7P>(qzDm|O$u~MR{5*U0>3Ssywc@VPY1|2Fpjp2%_VwnC(6qmLReFob6tty+?Xpa3WsDw)7EU9ZGoz4Hi0x%;RGF%@l`YnaU@o-(Cmw<WW*|jdCA6999|jXyX6zQvS`RxFG$F}<F7$FwN#;fLGKaLwv{OM0dB^C3T!xq;~wVn4XPs6nK2(T5=_~mlQ_01qhYrmG=nv?uYct~xH?a%#2G1T5=U!`CsCUR0QfRK<p3wfWGl`A<df;pZ8v%pXKp=WYtm8##(@761rnLC%7+bqQNP87157wst8aJILaI43*%k^#_-(FsJsM8(a0okQ_=@<qR<OmA8*?)=V9_bTxJ19?MN<<_-}N0FlUAjYK^|8t27nORyI3ncNYdU?7jk=TG;XZ*{Xl{BQRs0RR*6Vs8;wLi8*Pz0VruLdZBwO?^3SztP?0R%ZcICYxly~Dcqr~q`nmJ{jbzYVI=w3e-XQ+2qE2u7J2#yLc~6~Uu>;Y1gDfK?9P(feFv4ZoD<L$8@2$Ns31Iuy;-a?&eA3=G%*rmAH=f2FTGeLhT1?G)zG_`2jg6GKUD1TCDsrT1xDiNxQIqJpE4ge&txu@&2QxqrQN>Hyr<^<xNbB-tJhtRq?9Ho@q2Q}i&!gU-y%W>kUJBYiY$z4&a<Y?qjr+)zuP<(PNVab8sZjc=bcj41Q)%eEJs3c?loW4;6r``d^%<3<oM4+%d&{qWf9{>e=KkZv^Cz!C%^QIM$e{qZz|Kl`c$#U0S34Jy<>aDNrWDSa$0?dzzz1y1d0vf8OiaEQ!F6AIG~)pI3;A&U?Yi#O<fpOK4`Z?Ci|~O9%K*cKx&llPkVqL?z7I7`Z`<QclEempInFOW#_}2^SKhfd@^ajXjC3I5RT|+Mn5i2TY%|sGye_uQe}=cq`qYRerS<g+q1j_6s^MJ4;Wz`22pycCZDJPas=*sZ#SqU-G~xk_HC_7cE}7d5IeJ+(S7LNMOl5wfSD|Jsc|Az(^lnn%jK>MPfz)+%m5k~}oKE^)<0a+8=0#psg)`+Kv$nU#K|nhNA2pFOV*AaNnOiyQ@=~6zB_fa@<#=_TrK!0+uCpc@v)+*U{Slp2&qNlnna&pxbGQRqvlg}3DA5jmci55NHZ^)JtJgrtq#kZlmAeh866<$JzyTwr#sj+}9p7#52<hsJ<uZQ^54W4pb-r(N^jnlWa!2GxaZikckKjlv`VbgLnuZAP+$w$0aJg@jnz8<N_osHP|EJg4_@6A$`_q%pr%0Bbj68h`IKmg+scF5Q9zA^Y!#CeP{N~%gfAiuIU4qW~A0Ymy5&')).decode("utf-8"))
CATALOG = {'version': 'user-list-2026-10-17', 'source_id': 'U-GROUPS-20261017', 'source': '用户于2026-10-17在本次对话提供的8组大类清单', 'verification': 'user_provided_not_officially_verified', 'applicable_cohort': '未提供，不推定为2026级', 'rule': '本专业大类内专业任选；仅按用户提供文本记录，不推导跨大类资格', 'groups': {'future': {'name': '未来产业精英', 'display_name': '未来产业精英', 'majors': ['智能科学与技术（具身与行为智能特色班）', '智能医学工程（脑机接口特色班）', '新能源科学与工程（数智能源特色班）', '材料化学（新材料特色班）', '生物技术（生物智造特色班）']}, 'information': {'name': '信息科学与技术', 'display_name': '信息科学与技术', 'majors': ['计算机科学与技术', '物联网工程', '信息安全', '自动化', '智能科学与技术', '软件工程']}, 'physics_opto': {'name': '物理与光电信息技术工程', 'display_name': '物理与光电信息技术工程', 'majors': ['物理学', '应用物理学', '光电信息科学与工程', '电子信息科学与技术', '微电子科学与工程', '电子科学与技术', '通信工程']}, 'matter': {'name': '物质科学', 'display_name': '物质科学', 'majors': ['化学', '应用化学', '生物科学', '材料物理', '材料化学']}, 'digital_finance': {'name': '数智经济金融', 'display_name': '数智经济金融', 'majors': ['数字经济', '金融科技']}, 'boqin_info': {'name': '卓越拔尖计划伯芩班', 'display_name': '卓越拔尖计划伯芩班（信息方向，用于界面区分）', 'majors': ['计算机科学与技术', '智能科学与技术', '光电信息科学与工程']}, 'math_data': {'name': '数学与大数据', 'display_name': '数学与大数据', 'majors': ['数学与应用数学', '信息与计算科学', '统计学', '数据科学']}, 'boqin_science': {'name': '卓越拔尖计划伯芩班', 'display_name': '卓越拔尖计划伯芩班（理科方向，用于界面区分）', 'majors': ['物理学', '量子信息科学', '化学', '生物科学']}}, 'package_version': '2.0.0', 'naming_notes': ['官方2026报道使用伯苓；用户最初清单使用伯芩。两组成员分别保留，不把单独班名映射为确定组。', '官方报道可以提供专业与特色方向背景，不能无声改写用户的组内专业集合或个人资格。']}
CASE_VERSION = '2026-10-17.v4.0'
FAMILY_NAMES = {'route': '网络与路径', 'sensor': '阈值与误判', 'control': '反馈与动态', 'experiment': '实验对照', 'evidence': '数据与证据', 'resource': '资源与权衡', 'debug': '排错与系统', 'materials': '材料与性能', 'finance': '经济与决策', 'story': '叙事两难', 'values': '价值排序', 'hearing': '优先级听证', 'daylife': '一天拼图', 'failure': '失败复盘'}
ALIASES = {"senor": "sensor"}
DEFAULTS = {"route":"route_campus", "sensor":"sensor_luggage", "control":"control_cart"}
# Per-group activity menus. Only families listed here appear as buttons for a
# confirmed group; a student can still reach any family by explicitly naming it.
GROUP_FAMILIES = {
    "future":["experiment","materials","resource","sensor","control","story","hearing","daylife","failure"],
    "information":["debug","route","sensor","control","evidence","story","values","hearing","failure"],
    "physics_opto":["materials","sensor","control","debug","evidence","story","values","hearing","daylife"],
    "matter":["experiment","materials","evidence","resource","values","hearing","daylife","failure"],
    "digital_finance":["finance","resource","evidence","story","values","daylife","failure"],
    "boqin_info":["route","debug","sensor","materials","values","hearing","daylife"],
    "math_data":["evidence","resource","route","finance","story","values","hearing","daylife","failure"],
    "boqin_science":["experiment","evidence","materials","values","daylife","failure"],
}
DEFAULT_MENU_FAMILIES = ["story","values","hearing","daylife","failure","evidence","resource","experiment"]
STOP_WORDS = {"结束", "退出", "结束体验", "不做了", "停止体验"}
HINT_WORDS = {"提示", "给我提示", "求助", "不会", "不知道", "不确定"}
CONFIRM_WORDS = {"确认", "确认试算", "确认方案", "按此试算", "确认计算", "保持方案"}
GATE_CANCEL_WORDS = {"先不生成", "再想想", "继续", "先不要", "先不结束", "再看看", "取消", "先不了", "继续体验"}
NEW_MODES = ("rank", "allocation", "compose")


def markdown_text(value):
    """Display untrusted prose literally. Exact raw text stays in state/events."""
    value = html.escape(str(value), quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|>~\-])", r"\\\1", value)


def quoted(value):
    return "\n".join("> " + markdown_text(line) if line else ">" for line in str(value).split("\n"))


def looks_like_question(text):
    return bool(re.search(r"(?:怎么|如何|能否|可不可以|会不会|有没有|什么时候|什么是|为什么|哪|吗|么)", text))


def wants_finish(raw):
    """Conservative explicit intent detector; do not act on reported/negative speech."""
    text = raw.strip().rstrip("。！？!? ")
    # Students may quote UI instructions or negate a past wish; these are not commands.
    if not text or re.search(r"[“”\"‘’]|(?:并不|不是|不要|不想|不用|无需|不需要|还不|先不|暂不|不能|别|不)(?:[^，,。；;]{0,5})(?:结束|退出|停止|报告)|(?:如果|假如|要是|比如|示例|有人说|你说的|上次|之前|刚才|结束后)", text):
        # '不想继续' is itself an explicit stop request, not a negated stop.
        if not re.fullmatch(r"(?:我)?(?:不想|不打算|不愿意)再?继续(?:做|体验|答题|回答)?了?(?:[，,；;\s]*(?:请)?(?:帮我|给我|为我)?(?:生成|整理|出|拿到|看看|提供)?(?:一下)?(?:本次|当前|一份|已有)?(?:的)?(?:报告|记录))?[吧了]?", text):
            return False
    if text in STOP_WORDS or text in {"生成报告", "给我报告", "给我一份报告", "我要报告", "先看报告", "查看报告", "拿报告", "直接拿报告", "直接拿到报告", "结束并给我报告", "结束并生成报告", "结束并查看报告", "查看已有记录", "先到这里", "先到这吧", "到这里吧", "不继续了", "不想继续了", "生成记录", "直接生成记录", "整理记录", "给我记录", "我要记录", "查看记录"}:
        return True
    if looks_like_question(text):
        return False
    if re.search(r"(?:不想|不打算|不愿意)再?继续|(?:想|要|打算|决定|希望)(?:先|现在|直接)?(?:结束|退出|停止)(?:本次|这次|这个)?(?:体验|活动|练习|答题)?|(?:^|[，,；;\s])(?:我)?(?:现在|先|就|请)?(?:结束|退出|停止)(?:本次|这次|这个)?(?:体验|活动|练习|答题)?(?:[，,；;\s]|$|并|吧|了)|(?:直接|现在|就|先|请|帮我).{0,6}(?:拿到|拿|给我|生成|看|出)(?:本次|当前|已有|一份|的)*(?:报告|记录)", text):
        return True
    return False


def stage_guide(state):
    evaluated = sum(e.get("kind") == "evaluated" for e in state.get("events", []))
    if state.get("status") in ("stopped", "completed"):
        return "*本次体验已结束。下面保留你实际做过的内容；需要时可以再开始一次。*"
    if state.get("report_gate"):
        return "**现在：确认是否整理记录**\n\n*整理前你可以自愿留下一句这次的想法；不想留可以直接生成。还没做的部分不会补写。*"
    if state.get("status") == "awaiting_record_confirmation":
        label = "核对记录"
    elif state.get("status") == "evaluated":
        label = "看看结果，再决定下一步"
    elif state.get("status") == "awaiting_confirmation":
        label = "核对你刚才的方案"
    else:
        label = "先试一个方案" if state.get("phase", 0) == 0 else "条件变了，再试一次"
    return "**现在：%s**\n\n*一轮体验会试一个方案，再看看条件变化后会怎样，最后由你决定是否整理一份探索记录。已试算%d次。你随时可以说“结束”，我会先问你要不要整理记录；没做的部分不会补写。*" % (label, evaluated)


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def loads(value):
    if isinstance(value, dict):
        return copy.deepcopy(value)
    if not isinstance(value, str) or len(value) > 300000:
        raise ValueError("JSON须为不超过300000字符的字符串或对象")
    def invalid(token):
        raise ValueError("拒绝非有限数字：" + token)
    result = json.loads(value, parse_constant=invalid)
    if not isinstance(result, dict):
        raise ValueError("JSON顶层必须是对象")
    return result


def clean_text(value, limit=6000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError("文本须为不超过%d字符的字符串" % limit)
    return value


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int,float)):
        raise ValueError("必须为有限数值，不能是布尔值")
    if not low <= value <= high:
        raise ValueError("数值须在%s至%s之间" % (low,high))
    if not math.isfinite(value):
        raise ValueError("必须为有限数值")
    return float(value)


def phase_value(phase):
    if type(phase) is not int or phase not in (0,1):
        raise ValueError("phase须为整数0或1")
    return phase


def _variants_of(case):
    variants = case.get("surface_variants")
    if not isinstance(variants, list) or not variants:
        return [{}]
    return [v if isinstance(v, dict) else {} for v in variants]


def _variant_of(case, state):
    variants = _variants_of(case)
    index = 0
    if state:
        index = state.get("variant_index", 0)
        if type(index) is not int or not 0 <= index < len(variants):
            index = 0
    return variants[index]


def _data_of(case, state):
    """Case data with the active variant's shallow overrides applied."""
    data = case["data"]
    overrides = _variant_of(case, state).get("data_overrides") if state else None
    if not overrides:
        return data
    merged = copy.deepcopy(data)
    merged.update(copy.deepcopy(overrides))
    return merged


def _fmt(text, case, state):
    """Substitute {surface_key} placeholders; leave {reason} for later stages."""
    if not isinstance(text, str) or "{" not in text:
        return text
    surface = _variant_of(case, state).get("surface", {}) if state else {}
    def repl(match):
        key = match.group(1)
        if key == "reason":
            return match.group(0)
        if key in surface:
            return str(surface[key])
        if state is None:
            return match.group(0)
        raise ValueError("变体缺少占位符：" + key)
    return re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", repl, text)


def _active_items(case, state):
    """Rendered item list (rank cards / allocation entries) for this state."""
    items = _data_of(case, state).get("items", [])
    by_id = {it["id"]: it for it in items if isinstance(it, dict) and "id" in it}
    ids = _variant_of(case, state).get("item_ids") if state else None
    if ids:
        ordered = [by_id[i] for i in ids if i in by_id]
        if ordered:
            items = ordered
    return [{"id": it["id"], "text": _fmt(it.get("text", ""), case, state)} for it in items]


def _option_perm(case, state):
    perm = state.get("option_perm") if state else None
    if isinstance(perm, list) and sorted(perm) == ["A", "B", "C"]:
        return list(perm)
    return ["A", "B", "C"]


def _display_to_original(case, state, letter):
    perm = _option_perm(case, state)
    if letter in ("A", "B", "C"):
        return perm[ord(letter) - 65]
    return letter


def _original_to_display(case, state, letter):
    perm = _option_perm(case, state)
    if letter in perm:
        return chr(65 + perm.index(letter))
    return letter


def _rendered_options(case, phase, state):
    raw = case["data"].get("options", [{}, {}])[phase]
    perm = _option_perm(case, state)
    return {letter: _fmt(raw.get(perm[i], ""), case, state) for i, letter in enumerate(("A", "B", "C"))}


def _budget_of(data, phase):
    budget = data.get("budget", 0)
    if isinstance(budget, list):
        return budget[phase] if phase < len(budget) else budget[-1]
    return budget


def case_of(state):
    if state.get("engine_version") != ENGINE_VERSION:
        raise ValueError("状态版本与当前引擎不兼容，请重新开始")
    cid = state.get("case_id")
    case = state.get("case_snapshot")
    if case is None:
        if cid not in BANK["cases"]:
            raise ValueError("未知案例")
        case = BANK["cases"][cid]
        if state.get("case_version") != BANK["case_version"]:
            raise ValueError("题库版本与当前状态不一致，请重新开始")
    else:
        if state.get("case_version") != CASE_VERSION:
            raise ValueError("题库版本与当前状态不一致，请重新开始")
        if case.get("case_id") != cid:
            raise ValueError("状态案例快照不一致")
    phase_value(state.get("phase"))
    if state.get("task_id") != case["task_id"]:
        raise ValueError("状态中任务与案例不一致")
    if state.get("group_id") not in set(CATALOG["groups"]) | {"unknown"}:
        raise ValueError("未知所属大类")
    if type(state.get("group_confirmed")) is not bool:
        raise ValueError("group_confirmed须为布尔值")
    if type(state.get("report_gate", False)) is not bool:
        raise ValueError("report_gate须为布尔值")
    variants = _variants_of(case)
    vi = state.get("variant_index", 0)
    if type(vi) is not int or not 0 <= vi < len(variants):
        raise ValueError("variant_index超出范围")
    perm = state.get("option_perm")
    if perm is not None and (not isinstance(perm, list) or sorted(perm) != ["A", "B", "C"]):
        raise ValueError("option_perm格式不正确")
    if not isinstance(state.get("events"), list) or len(state["events"]) > 160:
        raise ValueError("状态事件格式不正确或本次体验过长")
    return case


def _mode_of(case, state=None):
    if isinstance(state, dict):
        fam = state.get("family_snapshot")
        if fam is not None:
            return fam["mode"]
    return BANK["families"][case["task_id"]]["mode"]


def _group_relevant(case, group_id):
    if group_id in (None, "unknown") or group_id not in CATALOG["groups"]:
        return False
    own = set(CATALOG["groups"][group_id].get("majors", []))
    return bool(own & set(case.get("related_majors", [])))


def choose_case(params):
    task = ALIASES.get(params.get("task_id"), params.get("task_id", "auto")) or "auto"
    cid = params.get("case_id", "")
    variant = params.get("variant_id", "")
    excluded = params.get("exclude_case_ids", [])
    if not isinstance(excluded,list) or any(not isinstance(x,str) for x in excluded):
        raise ValueError("exclude_case_ids须为字符串数组")
    if cid and cid != "auto":
        if cid not in BANK["cases"]:
            raise ValueError("case_id不存在")
        if task not in ("auto", BANK["cases"][cid]["task_id"]):
            raise ValueError("task_id与case_id冲突")
        return cid
    if task != "auto" and task not in BANK["families"]:
        raise ValueError("未知task_id")
    if variant and variant != "auto":
        if task == "auto":
            raise ValueError("指定variant_id时须同时指定task_id")
        cid = task + "_" + str(variant)
        if cid not in BANK["cases"]:
            raise ValueError("variant_id不存在")
        return cid
    # Legacy task-only calls preserve original numeric fixtures.
    if task in DEFAULTS and "seed" not in params and not variant and not cid and DEFAULTS[task] not in excluded:
        return DEFAULTS[task]
    allowed = GROUP_FAMILIES.get(params.get("group_id"), list(BANK["families"])) if task == "auto" else [task]
    candidates = [c for c,v in BANK["cases"].items() if v["task_id"] in allowed]
    available = [c for c in candidates if c not in excluded]
    if not available:
        raise ValueError("当前候选案例均已排除，请清空已体验列表或更换活动")
    relevant = [c for c in available if _group_relevant(BANK["cases"][c], params.get("group_id"))]
    if relevant:
        available = relevant
    seed = str(params.get("seed", "0"))
    rank = int(hashlib.sha256((seed+"|"+str(params.get("group_id","unknown"))+"|"+task).encode("utf-8")).hexdigest(),16)
    return available[rank % len(available)]


PLAN_SCHEMAS = {
    "route":{"path":"按本人明确顺序填写节点字符串数组，须包含起终点", "reason":"本人理由，可为空，不得补写"},
    "sensor":{"threshold":"0至100的有限数值", "reason":"本人理由，可为空，不得补写"},
    "control":{"k":"0至2的有限数值", "reason":"本人理由，可为空，不得补写"},
    "choice":{"choice":"A或B或C，仅能有一个", "reason":"本人理由，可为空，不得补写"},
    "rank":{"order":"把题目给出的卡片按本人明确顺序排列：项目id字符串数组，每张卡片恰好出现一次", "reason":"本人理由，可为空，不得补写"},
    "allocation":{"allocation":"对象：每个事项id对应一个非负整数（单位见题面），所有事项都要出现，总和须正好等于题面总额", "reason":"本人理由，可为空，不得补写"},
    "compose":{"response":"本人写下的正文原文，不能为空，不得替本人改写", "title":"本人给正文起的标题，没有则为空字符串", "reason":"可为空"},
}


def normalize_context(case,phase,state=None):
    mode = _mode_of(case, state)
    schema = PLAN_SCHEMAS[mode]
    options = _rendered_options(case, phase, state) if mode == "choice" else case["data"].get("options",[{},{}])[phase]
    ctx = {"case_id":case["case_id"],"task_id":case["task_id"],"phase":phase,"mode":mode,"plan_fields":schema,"options":options,"extract_schema":{"action":"submit|hint|clarify|stop","plan":schema,"quote":"学生本轮原文连续片段","question":"需要时只问一个澄清问题"},"rule":"不代替用户选方案，不算结果，不判断专业适配；多备选须clarify，JSON只是候选，必须本人确认后计算。"}
    if mode in ("rank","allocation"):
        ctx["items"] = _active_items(case, state)
        ctx["budget"] = _budget_of(_data_of(case, state), phase) if mode == "allocation" else ""
    if mode == "compose":
        data = _data_of(case, state)
        ctx["writing"] = _fmt(data.get("writing", ["", ""])[phase], case, state)
        ctx["max_chars"] = data.get("max_chars", 800)
    return ctx


def task_text(case,phase,state=None):
    phase_value(phase)
    data=_data_of(case,state); mode=_mode_of(case,state)
    parts=["## "+case["title"], "*这是为理解工作方法编写的教学情境，数据为合成，不用来判断你的能力或专业适合程度。*", _fmt(case["context"],case,state),"### "+("先看看现在的情况" if phase==0 else "接下来，情况有了变化"),_fmt(case["phases"][phase],case,state)]
    if mode=="choice":
        evidence=data.get("evidence",["",""])
        if evidence[phase]: parts.append(_fmt(evidence[phase],case,state))
        rendered=_rendered_options(case,phase,state)
        parts += ["- **方案 "+key+"**："+text for key,text in rendered.items()]
        parts.append("**你会怎么做？**\n\n请点选一个做法。这里没有标准答案——几个做法往年都有人真选过；想补充自己的考虑，可以在核对时选择“我想改一下”再告诉我。还拿不准的话，可以先要一点提示。")
    elif mode=="route":
        parts.append("**可走的路段**（两个方向都能走）：\n\n| 路段 | 基础耗时 |\n| --- | --- |\n"+"\n".join("| %s ↔ %s | %s%s |"%(a,b,w,data["unit"]) for a,b,w in data["edges"]))
        parts.append("**你打算怎么走？**\n\n说出从%s到%s经过的地点，按先后顺序写就好，也可以补充你的考虑。"%(data["start"],data["end"]))
    elif mode=="sensor":
        parts.append("**这次用到的样本**\n\n1表示确实有需要检测的情况，0表示没有。\n\n| 检测分数 | 实际情况（1/0） |\n| --- | --- |\n"+"\n".join("| %s | %s |"%tuple(s) for s in data["samples"]))
        parts.append("**你会把分界线设在多少分？**\n\n选一个0到100的数。分数达到这个数，就算检测到了。也可以说说你更担心哪一种判断错误。")
    elif mode=="control":
        gain=data["gains"][phase]
        limit=data.get("limits",[data.get("limit",2)]*2)[phase]
        disturbance=data.get("disturbances",[0,0])[phase]
        parts.append("**这个简化模型怎样变化**\n\n- 起始位置：%s；希望到达的位置：%s。\n- 一共观察%s步。每一步先算“目标位置减去当前位置”，再乘你选的调整力度k。\n- 每一步的调整量最多为%s，反方向最多为−%s。\n- 下一步的位置 = 当前位置 + %s × 实际调整量 − %s。最后一项表示每一步受到的固定外部影响。"%(data["initial"],data["target"],data["steps"],limit,limit,gain,disturbance))
        parts.append("**希望看到的结果**\n\n最后一步离目标不超过%s；过程中超过目标的幅度不超过%s。"%(data["error_target"],data["overshoot_limit"]))
        parts.append("**你想用多大的调整力度？**\n\n用0到2之间的一个数表示，题目把它记作k。数值越大，每次根据偏差做出的调整越强。这里只观察这个简化模型里的变化。")
    elif mode=="rank":
        items=_active_items(case,state)
        parts.append("**这次要排序的卡片**\n\n"+"\n".join("- "+it["text"] for it in items))
        parts.append("**你会怎么排？**\n\n按题面要求说出先后顺序（例如“××第一，××第二……”），把每张卡片都排到，也可以补充你的理由。")
    elif mode=="allocation":
        items=_active_items(case,state)
        budget=_budget_of(data,phase); unit=data.get("unit",""); step=data.get("min_step") or 1; cap=data.get("max_per_item")
        parts.append("**这次要分配的事项**\n\n"+"\n".join("- "+it["text"] for it in items))
        rule="分配规则：总额 **%s%s**，必须正好分完；每项最小单位 %s%s，可以是 0。"%(budget,unit,step,unit)
        if cap is not None: rule+="单项最多 %s%s。"%(cap,unit)
        parts.append(rule)
        parts.append("**你会怎么分？**\n\n逐项说出各给多少，再说说你的理由。没有能让所有人都满意的方案，重要的是你按什么取舍。")
    else:
        writing=data.get("writing",["",""])
        parts.append("**这次的写作任务**\n\n"+_fmt(writing[phase],case,state))
        if data.get("title_prompt"): parts.append(_fmt(data["title_prompt"],case,state))
        parts.append("直接写下你的话就好；标题可以另起一行写“标题：……”。这段话不会被评分，会原样保留在你的记录里。")
    parts.append("*可以求提示，也可以随时结束；结束前我会先问你要不要整理记录。*")
    return "\n\n".join(parts)


def validate_plan(case, plan, state=None, phase=0):
    if not isinstance(plan,dict): raise ValueError("plan必须为对象")
    mode=_mode_of(case,state)
    key={"route":"path","sensor":"threshold","control":"k","choice":"choice","rank":"order","allocation":"allocation","compose":"response"}[mode]
    allowed={key,"reason"} | ({"title"} if mode=="compose" else set())
    if key not in plan or set(plan)-allowed: raise ValueError("本题仅接受%s和可选reason字段"%("、".join(sorted(allowed))))
    reason=clean_text(plan.get("reason",""),4000)
    if mode=="route":
        path=plan[key]; nodes={x for e in case["data"]["edges"] for x in e[:2]}
        if not isinstance(path,list) or not 2<=len(path)<=20 or any(not isinstance(x,str) or x not in nodes for x in path): raise ValueError("路线须为本题有效节点数组，长度2至20")
        if path[0]!=case["data"]["start"] or path[-1]!=case["data"]["end"]: raise ValueError("路线须包含本题起点与终点")
        value=list(path)
    elif mode=="choice":
        if plan[key] not in ("A","B","C"): raise ValueError("请明确选择A、B或C中的一个")
        value=plan[key]
    elif mode in ("sensor","control"):
        value=number(plan[key],0,100 if mode=="sensor" else 2)
    elif mode=="rank":
        ids=[it["id"] for it in _active_items(case,state)]
        order=plan[key]
        if not isinstance(order,list) or any(not isinstance(x,str) for x in order) or sorted(order)!=sorted(ids):
            raise ValueError("排序须把每张卡片恰好排入一次")
        value=list(order)
    elif mode=="allocation":
        data=_data_of(case,state)
        ids=[it["id"] for it in _active_items(case,state)]
        alloc=plan[key]
        if not isinstance(alloc,dict) or set(alloc)!=set(ids):
            raise ValueError("分配须恰好覆盖每个事项各一次")
        budget=_budget_of(data,phase); step=data.get("min_step") or 1; cap=data.get("max_per_item")
        if cap is None: cap=budget
        total=0
        for name,amount in alloc.items():
            if isinstance(amount,bool) or not isinstance(amount,int):
                raise ValueError("每项须为整数")
            if amount<0: raise ValueError("每项不能为负")
            if amount%step!=0: raise ValueError("每项须为最小单位%s的倍数"%step)
            if amount>cap: raise ValueError("单项最多%s"%cap)
            total+=amount
        if total!=budget: raise ValueError("各项总和须正好等于%s"%budget)
        value=dict(alloc)
    else:
        data=_data_of(case,state)
        limit=data.get("max_chars",800)
        response=clean_text(plan[key],max(limit*2,800))
        if not response.strip(): raise ValueError("正文不能为空")
        if len(response)>limit: raise ValueError("正文请在%s字以内"%limit)
        value=response
    result={key:value,"reason":reason}
    if mode=="compose":
        title=plan.get("title","")
        if not isinstance(title,str) or len(title)>40: raise ValueError("标题须为不超过40字的字符串")
        result["title"]=title.strip()
    return result


def parse_standard(case,text,state=None):
    """Conservative local correction parser; never selects among alternatives."""
    mode=_mode_of(case,state)
    if mode=="compose":
        base=text.strip()
        match=re.search(r"(?:^|[\n。！？；;，,])\s*标题[:：]\s*(.+)$", base)
        title=match[1].strip() if match else ""
        body=(base[:match.start()] if match else base).rstrip("。，,；; \n").strip()
        if body: return {"response":body,"title":title}
        return None
    raw=text.strip().replace("，",",").replace("。","")
    raw=re.sub(r"^(试算|选择|选|我选|改为|改成|那就|那|就用|就|设为|用)\s*", "", raw)
    raw=re.sub(r"吧$", "", raw).strip()
    if mode=="choice":
        match=re.fullmatch(r"([ABCabc])(?:[,:：;；\s]+(.+))?",raw)
        if match:return {"choice":match[1].upper(),"reason":match[2] or ""}
    elif mode in ("sensor","control"):
        raw=re.sub(r"^(?:阈值|threshold|k)\s*[=：:]?\s*", "", raw, flags=re.I)
        if re.fullmatch(r"(?:\d+(?:\.\d*)?|\.\d+)",raw):return {{"sensor":"threshold","control":"k"}[mode]:float(raw)}
    elif mode=="rank":
        ids=[it["id"] for it in _active_items(case,state)]
        parts=[x for x in re.split(r"[-－—→>,、\s]+",raw) if x]
        if len(parts)>1 and all(x in ids for x in parts): return {"order":parts}
    else:
        path=re.split(r"[-－—→>\s]+",raw.upper())
        if len(path)>1 and all(re.fullmatch(r"[A-Z]+",x) for x in path): return {"path":path}
    return None


def edge_weights(case,phase):
    d=case["data"]; blocked={frozenset(x) for x in d.get("blocked",[[],[]])[phase]}
    weights={frozenset((a,b)):w for a,b,w in d["edges"] if frozenset((a,b)) not in blocked}
    for a,b,w in d.get("edge_additions",[[],[]])[phase]:
        edge=frozenset((a,b))
        if edge in weights: weights[edge]+=w
    return weights


def shortest(case,phase):
    weights=edge_weights(case,phase); graph={}
    for edge,w in weights.items():
        a,b=tuple(edge); graph.setdefault(a,[]).append((b,w)); graph.setdefault(b,[]).append((a,w))
    start,end=case["data"]["start"],case["data"]["end"]
    q=[(0,start)]; dist={start:0}
    while q:
        score,node=heapq.heappop(q)
        if score!=dist[node]:continue
        if node==end:return score
        for other,w in graph.get(node,[]):
            value=score+w
            if value<dist.get(other,math.inf):dist[other]=value;heapq.heappush(q,(value,other))
    return None


def evaluate(case_id,plan,phase,state=None):
    phase_value(phase)
    snap=state.get("case_snapshot") if isinstance(state,dict) else None
    if snap is not None:
        if snap.get("case_id")!=case_id:raise ValueError("状态案例快照不一致")
        case=snap
    else:
        if case_id not in BANK["cases"]:raise ValueError("未知case_id")
        case=BANK["cases"][case_id]
    plan=validate_plan(case,plan,state,phase)
    mode=_mode_of(case,state); d=_data_of(case,state)
    out={"case_id":case_id,"task_id":case["task_id"],"case_version":CASE_VERSION or BANK["case_version"],"phase":phase,"kind":"synthetic_teaching_result","plan":plan}
    if mode=="choice":
        outcome=copy.deepcopy(d["outcomes"][phase][plan["choice"]])
        if isinstance(outcome.get("feedback"),str):
            template=_fmt(outcome["feedback"],case,state)
            reason_block=(quoted(plan["reason"])+"\n\n") if plan.get("reason") else ""
            outcome["feedback"]=template.replace("{reason}",reason_block)
        out.update(outcome);out["valid"]=True
    elif mode=="route":
        weights=edge_weights(case,phase); total=0; bad=[]
        for a,b in zip(plan["path"],plan["path"][1:]):
            edge=frozenset((a,b))
            if edge not in weights:bad.append(a+"-"+b+"不存在或已封闭")
            else:total+=weights[edge]
        minimum=shortest(case,phase); deadline=d.get("deadlines",[None,None])[phase]
        out.update(valid=not bad,problems=bad,minutes=None if bad else total,unit=d["unit"],reference_min_minutes=minimum,deadline=deadline,meets_deadline=(None if deadline is None or bad else total<=deadline),any_path_meets_deadline=(None if deadline is None or minimum is None else minimum<=deadline))
    elif mode=="sensor":
        counts=dict(tp=0,fp=0,fn=0,tn=0)
        for score,label in d["samples"]:
            predicted=int(score>=plan["threshold"])
            counts[{(1,1):"tp",(1,0):"fp",(0,1):"fn",(0,0):"tn"}[predicted,label]]+=1
        fpw,fnw=d["weights"][phase]
        out.update(valid=True,**counts,sample_count=len(d["samples"]),false_alarm_weight=fpw,miss_weight=fnw,loss=fpw*counts["fp"]+fnw*counts["fn"])
    elif mode=="rank":
        items=_active_items(case,state); texts={it["id"]:it["text"] for it in items}
        out.update(valid=True,order=plan["order"],item_order=[it["id"] for it in items],item_texts=texts,top_item=plan["order"][0],bottom_item=plan["order"][-1])
    elif mode=="allocation":
        items=_active_items(case,state); texts={it["id"]:it["text"] for it in items}
        budget=_budget_of(d,phase); unit=d.get("unit","")
        top=None
        for it in items:
            if top is None or plan["allocation"][it["id"]]>plan["allocation"][top]: top=it["id"]
        out.update(valid=True,allocation=plan["allocation"],budget=budget,unit=unit,item_order=[it["id"] for it in items],item_texts=texts,top_item=top)
    elif mode=="compose":
        out.update(valid=True,response=plan["response"],title=plan.get("title",""))
    else:
        gain=d["gains"][phase]; limit=d.get("limits",[d.get("limit",2)]*2)[phase]; disturbance=d.get("disturbances",[0,0])[phase]
        target=d["target"]; xs=[float(d["initial"])]; us=[]
        for _ in range(d["steps"]):
            u=max(-limit,min(limit,plan["k"]*(target-xs[-1])));us.append(u);xs.append(xs[-1]+gain*u-disturbance)
        error=abs(xs[-1]-target);overshoot=max(0,max(xs)-target)
        settled=next((i for i in range(1,len(xs)) if all(abs(x-target)<=d["error_target"] for x in xs[i:])),None)
        out.update(valid=True,gain=gain,target=target,disturbance=disturbance,actuator_limit=limit,trajectory=[round(x,6) for x in xs],controls=[round(x,6) for x in us],final_abs_error=round(error,6),max_overshoot=round(overshoot,6),within_observation_settled_step=settled,meets_teaching_target=error<=d["error_target"] and overshoot<=d["overshoot_limit"])
    return out


def feedback(result, state=None):
    if "feedback" in result:return "### 看看这个选择会怎样\n\n"+result["feedback"]+"\n\n*这只是对本题方案的反馈，不代表能力或专业适合程度。*"
    fam=state.get("family_snapshot") if isinstance(state,dict) else None
    mode=fam["mode"] if fam else BANK["families"].get(result.get("task_id"),{}).get("mode","")
    if mode=="rank":
        texts=result.get("item_texts",{})
        top=texts.get(result["top_item"],result["top_item"]); bottom=texts.get(result["bottom_item"],result["bottom_item"])
        reason_block=("你给出的理由：\n\n"+quoted(result["plan"].get("reason",""))+"\n\n") if result["plan"].get("reason") else ""
        return ("### 看看你的排序\n\n- 你排在第一的：**"+top+"**\n- 你排在最后的：**"+bottom+"**\n\n"+reason_block+
            "把「"+top+"」放在最前、把「"+bottom+"」放在最后——排序没有对错，它呈现的是这一次你在这些事物之间的取舍顺序。两个阶段连起来看，动了哪几张、为什么动，往往比顺序本身更值得回味。\n\n*这是一种倾向线索，不是能力判断，也不是专业匹配结论。*")
    if mode=="allocation":
        texts=result.get("item_texts",{}); unit=result.get("unit","")
        rows="\n".join("| %s | %s%s |"%(texts.get(k,k),result["allocation"][k],unit) for k in result.get("item_order",list(result["allocation"])))
        top=texts.get(result.get("top_item"),result.get("top_item",""))
        reason_block=("你给出的理由：\n\n"+quoted(result["plan"].get("reason",""))+"\n\n") if result["plan"].get("reason") else ""
        return ("### 看看你的分配\n\n| 事项 | 分给多少 |\n| --- | --- |\n"+rows+"\n\n"+reason_block+
            "这次你把最多的"+unit+"给了「"+top+"」。分配没有标准答案，它呈现的是你在几个互相冲突的诉求之间放的权重；别人把最多的给另一项，同样可能成立。\n\n*这是一种倾向线索，不是能力判断，也不是专业匹配结论。*")
    if mode=="compose":
        title_block="\n\n标题：「"+markdown_text(result["title"])+"」" if result.get("title") else ""
        return ("### 你写下的这段话\n\n"+quoted(result["response"])+title_block+"\n\n这段话不会被评分，也不会被用来推断能力或适合度；它会在你的探索记录里原样保留，含义由你自己决定。")
    if result["task_id"]=="route":
        if not result["valid"]:return "### 这条路暂时走不通\n\n"+"\n".join("- "+p for p in result["problems"])+"\n\n**这次没有计算总时长。**你可以换一条路再想想。"
        text="### 看看这条路线\n\n- **你的方案耗时：%s%s**\n- 当前路网中，最短路线耗时：%s%s"%(result["minutes"],result["unit"],result["reference_min_minutes"],result["unit"])
        if result["deadline"] is not None:text+="\n\n时限为%s，当前方案**%s按时到达**；给定路网中%s满足时限的路线。"%(result["deadline"],"可以" if result["meets_deadline"] else "不能","存在" if result["any_path_meets_deadline"] else "不存在")
        return text
    if result["task_id"]=="sensor":return "### 看看这条分界线的结果\n\n| 判断结果 | 条数 |\n| --- | --- |\n| 有情况，也检出了 | {tp} |\n| 没有情况，却报出了（误报） | {fp} |\n| 有情况，却漏掉了（漏报） | {fn} |\n| 没有情况，也没有报出 | {tn} |\n\n**总代价：{fp} × {false_alarm_weight} + {fn} × {miss_weight} = {loss}**\n\n*只适用于这批教学样本和题目给定的代价，不能直接代表真实设备效果。*".format(**result)
    return "### 看看调整之后的变化\n\n- 最后一步离目标还差：**{final_abs_error}**\n- 过程中超过目标的最大幅度：**{max_overshoot}**\n- 题目希望的结果：**{goal}**\n\n各步位置：{trajectory}\n\n*这是简化教学模型，短时间内的表现不能证明真实系统一直稳定。*".format(goal="达到了" if result["meets_teaching_target"] else "还没达到",**result)


def scope_majors(group_id,confirmed,majors):
    if not isinstance(majors,list) or any(not isinstance(x,str) for x in majors):raise ValueError("majors须为完整专业名称字符串数组")
    all_majors={m for g in CATALOG["groups"].values() for m in g["majors"]}
    own=CATALOG["groups"].get(group_id,{}).get("majors",[]) if confirmed else []
    scope={"within_group":[],"cross_group":[],"unverified":[],"group_confirmed":bool(confirmed),"catalog_source":CATALOG["source_id"],"catalog_verification":CATALOG["verification"]}
    for major in dict.fromkeys(majors):
        if not confirmed or group_id=="unknown" or major not in all_majors:scope["unverified"].append(major)
        elif major in own:scope["within_group"].append(major)
        else:scope["cross_group"].append(major)
    scope["notice"]="只按用户提供大类清单区分范围；不推导跨类转入、辅修资格，也不把活动关联专业直接变成推荐。"
    return scope


def add_event(state,kind,**data):
    if len(state["events"])>=160:raise ValueError("本次体验事件过多，请结束并新开一次")
    state["events"].append(dict(event_id=len(state["events"])+1,kind=kind,phase=state["phase"],**data))


def preview_plan(plan, case=None, phase=0, state=None):
    if plan is None:
        return "还没有一个明确的方案。"
    if "choice" in plan:
        letter=plan["choice"]
        display=_original_to_display(case,state,letter) if case else letter
        text="**你的选择：方案 "+display+"**"
        if case:
            raw=case["data"]["options"][phase][letter]
            text+="\n\n"+(_fmt(raw,case,state) if state else raw)
    elif "path" in plan:text="**你的路线："+" → ".join(plan["path"])+"**"
    elif "threshold" in plan:text="**你的分界线："+str(plan["threshold"])+"分**"
    elif "k" in plan:text="**你的调整力度："+str(plan["k"])+"**"
    elif "order" in plan:
        texts={it["id"]:it["text"] for it in _active_items(case,state)} if case else {}
        text="**你的排序：**\n\n"+"\n".join("%d. %s"%(i,texts.get(x,x)) for i,x in enumerate(plan["order"],1))
    elif "allocation" in plan:
        texts={it["id"]:it["text"] for it in _active_items(case,state)} if case else {}
        unit=_data_of(case,state).get("unit","") if case else ""
        text="**你的分配：**\n\n"+"\n".join("- %s：%s%s"%(texts.get(k,k),plan["allocation"][k],unit) for k in (texts.keys() if texts else plan["allocation"].keys()))
    else:
        text="**你写下的内容：**\n\n"+quoted(plan.get("response",""))
        if plan.get("title"):text+="\n\n标题：「"+markdown_text(plan["title"])+"」"
    if plan.get("reason"):text+="\n\n你给出的理由：\n\n"+quoted(plan["reason"])
    return text


def suggestion_lines(state, case):
    """Evidence-based next-step suggestions; never a score, ranking, or aptitude verdict."""
    completed=[e for e in state["events"] if e["kind"]=="evaluated"]
    lines=["## 下一步建议（依据你这次实际做过的内容）"]
    if not completed:
        lines.append("这次还没有试算任何方案，下面的建议只依据你选过的题目，依据较弱；如果愿意，可以先把这一题试完再看。")
    related=[m for m in case["related_majors"]]
    if state["group_confirmed"] and state["group_id"] in CATALOG["groups"]:
        scope=scope_majors(state["group_id"],True,related)
        if scope["within_group"]:
            lines.append("**与这次活动直接相关、且在你确认的大类内：** "+"、".join(markdown_text(m) for m in scope["within_group"]))
        rest=scope["cross_group"]+scope["unverified"]
        if rest:
            lines.append("**也相关，但不在你确认的大类内（跨类资格需另行核验）：** "+"、".join(markdown_text(m) for m in rest))
    elif related:
        lines.append("**与这次活动直接相关的专业方向：** "+"、".join(markdown_text(m) for m in related)+"\n\n*你还没有确认所属大类，这里不判断哪些专业对你可选。*")
    others=[fid for fid in GROUP_FAMILIES.get(state["group_id"],[]) if fid!=state["task_id"] and fid in FAMILY_NAMES]
    if not others:
        others=[fid for fid in FAMILY_NAMES if fid!=state["task_id"]]
    if others:
        picks="".join("「"+FAMILY_NAMES[fid]+"」" for fid in others[:2])
        lines.append("**再多一点依据：** 一次体验只呈现一种方法。建议再试一两类不同的活动，比如"+picks+"，把几次的感受放在一起比较，再下结论。")
    lines.append("**想深入了解某个专业：** 直接问我它“平时学什么课、做什么实验、毕业去向有哪些”，我会按知识库里的资料回答，并注明来源和年份。")
    lines.append("*这些建议只依据你本次实际完成并确认的内容和你写下的原话；不是测评分数，不是专业排名，也不是适合程度判断。*")
    return lines


def render_report(state):
    case=case_of(state); group=CATALOG["groups"].get(state["group_id"],{}).get("display_name","不清楚/暂不提供")
    completed=[e for e in state["events"] if e["kind"]=="evaluated"]
    cohort=state.get("cohort","")
    cohort_display="未提供；本次不据此判断年级资格" if cohort in ("","未知","跳过","未提供") else markdown_text(cohort)+"\n\n*由本人说明，未核验目录是否适用于该年级。*"
    lines=["# 本次专业活动探索记录", "**体验内容：** "+case["title"], "**所属大类：** "+markdown_text(group)+("（本人已确认）" if state["group_confirmed"] else "（尚未确认，暂不判断个人可选范围）"),"**入学年级：** "+cohort_display, "**记录状态：** "+("本人已确认整份记录" if state.get("record_confirmed") else "草稿。事实按已确认方案记录；整份记录尚未由本人确认")]
    if completed:
        phases={e["phase"] for e in completed}
        progress="已经试过初始方案和条件变化后的方案" if phases=={0,1} else "已经试过初始方案；还没有确认条件变化后的新方案"
        lines.append("## 这次实际做了什么\n\n"+progress+"。以下只列出实际完成的内容。")
    else:
        lines.append("## 这次实际做了什么\n\n还没有确认并试算任何方案，因此没有计算结果。已经提出但未确认的方案会单独列出。")
    for event in state["events"]:
        if event["kind"] in ("evaluated","recomputed"):
            label=("条件变化后，重新检查原方案" if event["kind"]=="recomputed" else ("第一次：本人确认的方案" if event["phase"]==0 else "条件变化后：本人确认的新方案"))
            chosen=preview_plan(event["plan"],case,event["phase"],state)
            lines += ["## "+label,chosen]
            if event.get("proposal_raw"):
                lines += ["你当时说的是：\n\n"+quoted(event["proposal_raw"])]
            lines.append(feedback(event["result"],state))
    if state.get("pending_plan"):
        lines += ["## 已提出、还没确认的方案", preview_plan(state["pending_plan"],case,state["phase"],state),"*这个方案没有作为你的正式选择，也没有试算。*", "你的原话：\n\n"+quoted(state.get("pending_raw",""))]
    elif state.get("unfinished_plan"):
        pending=state["unfinished_plan"]
        lines += ["## 已提出、还没确认的方案",preview_plan(pending["plan"],case,pending["phase"],state),"*结束前尚未确认，没有试算，也没有改写前面的结果。*","你的原话：\n\n"+quoted(pending.get("raw",""))]
    reflection=state.get("reflection_raw","")
    lines += ["## 你对这次体验的感受"]
    if reflection:
        lines += [quoted(reflection), "*"+("这段感受已随记录由本人确认。" if state.get("record_confirmed") else "保留本人原话；这段感受尚未随整份记录确认。")+"*"]
    else:
        lines += ["你在整理记录前选择不填写感受，或当时还没有填写。不会根据做题结果替你补写兴趣判断。"]
    lines += ["## 这次接触到了什么", "**涉及的方法：** "+"、".join(case["knowledge_tags"]),"**还没有体验：** "+case["boundary"],"*这些关联只帮助你继续了解专业，不是推荐或适合程度排名。*"]
    if state.get("requested_majors"):
        lines.append("## 你想继续了解的专业")
        scope=scope_majors(state["group_id"],state["group_confirmed"],state["requested_majors"])
        for k,label in [("within_group","按用户清单在本大类内，可继续了解"),("cross_group","跨大类兴趣，转入资格未核验"),("unverified","所属范围待核验")]:
            if scope[k]:lines.append("**"+label+"：** "+"、".join(markdown_text(m) for m in scope[k]))
    lines += suggestion_lines(state,case)
    lines += ["## 接下来可以怎么了解", "挑出刚才你最想继续追问的一点，再看一份相关专业的入门材料、真实课程或实验介绍，比较其中哪些事情你还愿意亲手尝试。", "*资料边界：大类目录来自用户提供的清单，尚未按个人年级核验分流规则。案例使用合成教学数据；建议部分只依据你实际完成的内容，没有测量能力、人格或专业适合程度，也不做专业排名。*"]
    return "\n\n".join(lines)


def gate_prompt(state):
    """Explicit pre-report question. The record is never rendered before this."""
    case=case_of(state)
    evaluated=sum(e.get("kind")=="evaluated" for e in state.get("events",[]))
    lines=["## 要现在为你整理这次的探索记录吗？",
        "本次体验："+case["title"]+"。已确认并试算 **%d** 个方案；没完成的部分不会补写。"%evaluated,
        "整理之前还有一件**完全自愿**的事：你可以留下一句这次的想法——印象最深的一刻、一句吐槽，或者给这次体验起个一句话标题都可以。你的想法会原样写进记录。",
        "- 想留一句：直接把你的想法告诉我；",
        "- 不想留：说“生成记录”，或点页面上的「直接生成记录」；",
        "- 还不想结束：点「先不生成」，回到刚才的内容，记录不会生成。"]
    return "\n\n".join(lines)


def _report_final(state, raw, skip_reflection=False):
    """Render the record after explicit gate consent; thoughts only from this explicit entrance."""
    if state["status"] in ("stopped","completed"):
        return response(state,"report",report=render_report(state))
    if state.get("pending_plan"):
        state["unfinished_plan"]={"plan":copy.deepcopy(state["pending_plan"]),"raw":state.get("pending_raw",""),"phase":state["phase"]}
        state["pending_plan"]=None
    text=raw.strip()
    if text and not skip_reflection:
        state["reflection_raw"]=text;add_event(state,"reflection",raw_text=text,at_report_gate=True)
    elif not state.get("reflection_raw"):
        add_event(state,"reflection_skipped",raw_text="",at_report_gate=True)
    state["report_gate"]=False;state["record_confirmed"]=False;state["status"]="awaiting_record_confirmation"
    add_event(state,"report_generated")
    return response(state,"report_ready",report=render_report(state),
        feedback_text="记录已经在上面了，请核对一下：\n\n- 准确：点「记录准确，完成体验」；\n- 想法想改：点「改一下我的想法」，改完再核对一次；\n- 先不确认：点「先不确认，保留」，记录会如实标注尚未确认。")


def _resume_current(state, case):
    state["report_gate"]=False
    if state.get("status")=="evaluated" and state.get("last_result"):
        return response(state,"resumed",feedback_text="好的，还没有生成记录，我们接着刚才的内容。\n\n"+feedback(state["last_result"],state))
    if state.get("status")=="awaiting_confirmation" and state.get("pending_plan"):
        return response(state,"resumed",preview="### 继续核对这个方案\n\n"+preview_plan(state["pending_plan"],case,state["phase"],state),feedback_text=correction_format(case,state))
    return response(state,"resumed",task_text(case,state["phase"],state),feedback_text="好的，还没有生成记录，我们接着刚才的内容。")


def response(state=None,action="ready",prompt="",preview="",feedback_text="",result=None,report="",**extra):
    out=dict(ok=True,action=action,state_json=dumps(state) if state is not None else "",prompt=prompt,preview=preview,feedback=feedback_text,result_json=dumps(result) if result is not None else "",report=report,error="")
    if state is not None:
        case=case_of(state);out.update(case_id=state["case_id"],task_id=state["task_id"],phase=state["phase"],title=case["title"],variant_id=case["variant_id"],normalizer_context=dumps(normalize_context(case,state["phase"],state)),knowledge_query=" ".join([case["title"]]+case["knowledge_tags"]+case["related_majors"][:3]))
    out.update(extra)
    pieces=[x for x in (report,preview,feedback_text) if x] if report else [x for x in (stage_guide(state) if state is not None else "",prompt,preview,feedback_text) if x]
    out["display_text"]="\n\n".join(pieces)
    return out


def dispatch(params):
    state=None
    original_state=None
    try:
        params=loads(params);op=params.get("op","catalog")
        if op=="catalog":return response(action="catalog",catalog_json=dumps({"engine_version":ENGINE_VERSION,"case_version":BANK["case_version"],"families":BANK["families"],"cases":[{"case_id":c["case_id"],"task_id":c["task_id"],"variant_id":c["variant_id"],"title":c["title"]} for c in BANK["cases"].values()],"groups":CATALOG["groups"],"group_families":GROUP_FAMILIES}))
        if op=="start":
            group=params.get("group_id","unknown") or "unknown"
            if group not in set(CATALOG["groups"])|{"unknown"}:raise ValueError("group_id不存在；两个伯芩班须按方向区分，不能只凭同名猜测")
            confirmed=params.get("group_confirmed",False)
            if type(confirmed) is not bool:raise ValueError("group_confirmed须为布尔值")
            if group=="unknown":confirmed=False
            selection=dict(params)
            if not confirmed:selection["group_id"]="unknown"
            cid=choose_case(selection);case=BANK["cases"][cid]
            seed=str(params.get("seed","") or "")
            variants=_variants_of(case)
            variant_index=0
            if seed and case.get("surface_variants"):
                variant_index=int(hashlib.sha256((seed+"|variant|"+cid).encode("utf-8")).hexdigest(),16)%len(variants)
            option_perm=None
            if seed and case.get("surface_variants") and BANK["families"][case["task_id"]]["mode"]=="choice":
                letters=["A","B","C"];h=int(hashlib.sha256((seed+"|perm|"+cid).encode("utf-8")).hexdigest(),16)
                for i in range(2,0,-1):
                    j=h%(i+1);letters[i],letters[j]=letters[j],letters[i];h//=3
                if letters!=["A","B","C"]:option_perm=letters
            state=dict(engine_version=ENGINE_VERSION,case_version=CASE_VERSION or BANK["case_version"],case_id=cid,task_id=case["task_id"],phase=0,status="awaiting_plan",group_id=group,group_confirmed=confirmed,cohort=clean_text(params.get("cohort","未知"),80),events=[],pending_plan=None,reflection_raw="",requested_majors=[],record_confirmed=False,variant_index=variant_index,option_perm=option_perm,report_gate=False,case_snapshot=case,family_snapshot=BANK["families"][case["task_id"]])
            add_event(state,"started",group_id=group,group_confirmed=confirmed)
            return response(state,"awaiting_plan",task_text(case,0,state))
        state=loads(params.get("state_json",""));original_state=copy.deepcopy(state);case=case_of(state)
        raw=clean_text(params.get("user_text",""));text=raw.strip().rstrip("。！! ")
        if op=="scope":
            scope=scope_majors(state["group_id"],state["group_confirmed"],params.get("majors",[]))
            return response(state,"scope_checked",scope_json=dumps(scope))
        if op=="report_final":
            return _report_final(state,raw,bool(params.get("skip_reflection")))
        if op=="report_cancel":
            return _resume_current(state,case)
        if op in ("stop","finish","hint") or wants_finish(raw) or (text in HINT_WORDS and op in ("propose","confirm")):
            is_stop=op in ("stop","finish") or wants_finish(raw)
            if is_stop:
                if state["status"] in ("stopped","completed"):
                    return response(state,"report",report=render_report(state))
                if state.get("report_gate"):
                    # The gate was already shown; a fresh explicit finish is consent to render now.
                    return _report_final(state,raw,skip_reflection=True)
                state["report_gate"]=True
                return response(state,"report_gate",feedback_text=gate_prompt(state))
            if state["status"] in ("stopped","completed"):
                return response(state,"report",report=render_report(state))
            state["report_gate"]=False
            add_event(state,"hint",raw_text=raw)
            return response(state,"hint",task_text(case,state["phase"],state),feedback_text="### 给你一点提示\n\n"+_fmt(case["hint"],case,state)+"\n\n你可以继续想一个方案，也可以先结束；结束前我会先问你要不要整理记录。")
        if op=="report":return response(state,"report",report=render_report(state))
        if state["status"] in ("stopped","completed"):
            return response(state,"report",report=render_report(state))
        if state.get("report_gate") and op=="propose":
            # Natural-language answers while the report gate is open.
            if text in GATE_CANCEL_WORDS:
                return _resume_current(state,case)
            if looks_like_question(text):
                return response(state,"clarify",feedback_text="你是想留一句想法、直接生成记录，还是先不生成、继续刚才的内容？告诉我你的意思就好。")
            return _report_final(state,raw,skip_reflection=False)
        if op=="propose":
            if state["status"] not in ("awaiting_plan","awaiting_confirmation"):raise ValueError("当前阶段已计算；请advance或reflect，不重复覆盖事实")
            candidate=loads(params["candidate_json"]) if params.get("candidate_json") else {}
            action=candidate.get("action",params.get("candidate_action","submit"))
            if action in ("stop","finish") and not wants_finish(raw):
                return response(state,"clarify",feedback_text="你是想继续试一个方案，还是先到这里、看看目前的记录？我会按你的意思继续。")
            if action in ("stop","finish","hint"):
                return dispatch({"op":action,"state_json":dumps(state),"user_text":raw})
            if action=="clarify":
                state["pending_plan"]=None;state["status"]="awaiting_plan";add_event(state,"clarification",raw_text=raw)
                question=clean_text(candidate.get("question", "你想先试哪一个方案？可以选定一个，也可以先要一点提示。"),300)
                return response(state,"clarify",task_text(case,state["phase"],state),feedback_text="### 我想确认一下\n\n"+markdown_text(question))
            if action!="submit":raise ValueError("未知候选action")
            plan=candidate.get("plan")
            if plan is None and params.get("plan_json"):plan=loads(params["plan_json"])
            if plan is None:plan=parse_standard(case,raw,state)
            if plan is None:return response(state,"clarify",task_text(case,state["phase"],state),feedback_text="### 我还没听清你的选择\n\n你想先试哪一个方案？可以直接说一个明确的选择，也可以先要一点提示。")
            mode=_mode_of(case,state)
            if mode=="choice" and isinstance(plan,dict) and plan.get("choice") in ("A","B","C"):
                plan=dict(plan);plan["choice"]=_display_to_original(case,state,plan["choice"])
            plan=validate_plan(case,plan,state,state["phase"])
            if not raw.strip():raise ValueError("候选方案必须绑定学生本轮非空原文")
            if plan.get("reason") and plan["reason"] not in raw:raise ValueError("方案理由须保留学生本轮连续原话，不可替本人改写或补充")
            quote=candidate.get("quote",raw)
            if not isinstance(quote,str) or not quote or quote not in raw:raise ValueError("提取quote不是学生本轮原文连续片段")
            state["pending_plan"]=plan;state["pending_raw"]=raw;state["status"]="awaiting_confirmation";add_event(state,"proposed",raw_text=raw,plan=plan)
            return response(state,"awaiting_confirmation",preview="### 先核对一下，我有没有理解对\n\n"+preview_plan(plan,case,state["phase"],state)+"\n\n如果对，选择“就按这个试”。想改的话，请先选择“我想改一下”，再告诉我新方案。",feedback_text=correction_format(case,state))
        if op=="confirm":
            if state["status"] not in ("awaiting_confirmation","awaiting_plan"):raise ValueError("当前没有等待确认的方案")
            pending=state.get("pending_plan");plan=None;explicit_replacement=False
            if text in CONFIRM_WORDS|{"按这个方案试一试","就按这个试","就按这个试试","试试这个方案","可以，就这样","对，就这个","没错","准确","对"} and pending is not None:plan=pending
            elif text.startswith("试算") or text.startswith("更正并确认"):
                explicit_replacement=True
                confirmed_input=re.sub(r"^更正并确认[:：]?\s*", "", text)
                plan=parse_standard(case,confirmed_input,state)
                if plan is not None:
                    if _mode_of(case,state)=="choice" and plan.get("choice") in ("A","B","C"):
                        plan["choice"]=_display_to_original(case,state,plan["choice"])
                    plan=validate_plan(case,plan,state,state["phase"])
            else:
                # A correction becomes a new visible candidate, not an unconfirmed result.
                standard=parse_standard(case,raw,state)
                if standard is not None:return dispatch({"op":"propose","state_json":dumps(state),"user_text":raw,"plan_json":dumps(standard)})
            if plan is None:
                current=preview_plan(pending,case,state["phase"],state) if pending else "还没有一个明确的方案。"
                return response(state,"need_confirmation",preview="### 还没有开始试算\n\n"+current+"\n\n你是想按这个方案试一试，还是改成别的？如果还拿不准，也可以先要一点提示。",feedback_text=correction_format(case,state))
            result=evaluate(state["case_id"],plan,state["phase"],state)
            add_event(state,"evaluated",plan=plan,result=result,confirmation_raw=raw,proposal_raw=raw if explicit_replacement else state.get("pending_raw",raw))
            state["last_plan"]=plan;state["last_result"]=result;state["pending_plan"]=None;state["status"]="evaluated"
            return response(state,"evaluated",feedback_text=feedback(result,state),result=result,reflection_prompt=case["reflection"])
        if op=="advance":
            if state["phase"]!=0 or state["status"]!="evaluated":raise ValueError("仅第一阶段已计算后可进入条件变化")
            state["phase"]=1;state["status"]="awaiting_plan";state["pending_plan"]=None
            mode=_mode_of(case,state)
            if mode=="choice":
                old=state["last_plan"]["choice"]
                add_event(state,"conditions_changed",previous_choice=old,previous_option=case["data"]["options"][0][old])
                return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="### 回头看看刚才的选择\n\n你刚才选择的是：\n\n"+quoted(_fmt(case["data"]["options"][0][old],case,state))+"\n\n**这次的条件和选项都变了，请重新看过后再选。**同一个字母，可能已经是另一个方案。")
            if mode in NEW_MODES:
                last=copy.deepcopy(state["last_plan"])
                add_event(state,"conditions_changed",previous_plan=last)
                return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="### 回头看看刚才\n\n"+preview_plan(last,case,0,state)+"\n\n**这次的条件变了，请重新看过后再做。**可以沿用刚才的思路，也可以完全推翻；两次放在一起看，变化的地方最有意思。")
            result=evaluate(state["case_id"],state["last_plan"],1,state);add_event(state,"recomputed",plan=state["last_plan"],result=result)
            return response(state,"awaiting_plan",task_text(case,1,state),feedback_text="## 如果沿用刚才的方案\n\n"+feedback(result,state),result=result)
        if op=="reflect":
            if state["status"] not in ("evaluated","awaiting_record_confirmation"):raise ValueError("先完成一个明确方案，才生成探索草稿")
            majors=params.get("majors",[])
            scope=scope_majors(state["group_id"],state["group_confirmed"],majors)
            skip_reflection=text in {"跳过","先跳过","暂时跳过","不知道","不确定","还没想好","暂时没想好","没有","暂不填写","先不填"}
            state["reflection_raw"]="" if skip_reflection else raw;state["record_confirmed"]=False;state["status"]="awaiting_record_confirmation";state["requested_majors"]=majors
            add_event(state,"reflection_skipped" if skip_reflection else "reflection",raw_text=raw)
            return response(state,"awaiting_record_confirmation",preview="### 请看看这份记录\n\n准确的话，可以选择“确认记录”。感受想修改的话，直接告诉我完整的新说法；也可以先保留这份未确认的记录。",report=render_report(state),scope_json=dumps(scope))
        if op=="confirm_record":
            if state["status"]!="awaiting_record_confirmation":raise ValueError("当前没有待确认记录")
            if text.startswith("更正并确认：") or text.startswith("更正并确认:"):
                revised=re.split("[:：]",raw,maxsplit=1)[1]
                if not revised.strip():raise ValueError("更正反思不能为空")
                state["reflection_raw"]=revised
            elif text not in ("确认记录","确认","记录准确","没问题，确认","确认保存"):
                if text in ("先不确认","先保留这份记录","保留未确认记录","跳过","暂不确认"):
                    state["status"]="completed";add_event(state,"record_unconfirmed",raw_text=raw)
                    return response(state,"record_unconfirmed",report=render_report(state))
                # A replacement reflection remains visibly unconfirmed until the student accepts it.
                state["reflection_raw"]=raw;state["record_confirmed"]=False;add_event(state,"reflection_revised",raw_text=raw)
                return response(state,"need_record_confirmation",preview="### 已按你的原话更新感受\n\n请再看看记录，准确的话选择“确认记录”；也可以先保留这份未确认的记录。",report=render_report(state))
            state["record_confirmed"]=True;state["status"]="completed";add_event(state,"record_confirmed",raw_text=raw)
            return response(state,"completed",report=render_report(state))
        raise ValueError("未知op")
    except (ValueError,TypeError,KeyError,IndexError,AttributeError) as exc:
        # Retain the last valid input state for a recoverable correction where possible.
        message="这一步还没有完成，刚才已经确认过的内容仍保留在本次记录里。你可以换个说法继续，也可以直接结束并查看报告。"
        report=""
        if original_state is not None:
            try:report=render_report(original_state)
            except (ValueError,TypeError,KeyError,IndexError,AttributeError):pass
        if not report:
            message="这一步没有成功开始，因此还没有生成新的计算结果。你可以重新开始；如果你手里有先前的报告，可以继续按那份报告查看。"
        return dict(ok=False,action="error",state_json=dumps(original_state) if original_state is not None else "",prompt="",preview="",feedback=message,result_json="",report=report,display_text="### 需要再确认一下\n\n"+message+"\n\n*已确认的内容仍在；想整理完整记录时，说「生成记录」即可。*",normalizer_context="",knowledge_query="",error=str(exc))


def correction_format(case, state=None):
    mode=_mode_of(case, state)
    return {"choice":"*想修改请先选择“我想改一下”，再说明你想换成哪种做法，也可以补充理由。*", "route":"*想修改请先选择“我想改一下”，再按经过顺序写出整条路线，例如S-A-T；请使用题目中的地点。*", "sensor":"*想修改请先选择“我想改一下”，再说你想把分界线改成多少分。*", "control":"*想修改请先选择“我想改一下”，再告诉我新的调整力度，用0到2之间的数表示。*", "rank":"*想修改请先选择“我想改一下”，再按新顺序把每张卡片说一遍。*", "allocation":"*想修改请先选择“我想改一下”，再逐项说出新的分配，总和须正好等于题面总额。*", "compose":"*想修改请先选择“我想改一下”，再把你想写的内容完整重写一遍。*"}[mode]


def handler(params):
    return dispatch(params)


async def main(params):
    """Optional NK-GeniOS code-node wrapper; params may wrap inputs in params['input']."""
    if isinstance(params,dict) and "input" in params and "op" not in params:params=params["input"]
    return dispatch(params)


_core_handler = handler
MAJOR_NAMES = ['计算机科学与技术', '物联网工程', '信息安全', '自动化', '智能科学与技术', '软件工程', '物理学', '应用物理学', '光电信息科学与工程', '电子信息科学与技术', '微电子科学与工程', '电子科学与技术', '通信工程', '数学与应用数学', '信息与计算科学', '统计学', '数据科学', '量子信息科学', '化学', '应用化学', '生物科学', '材料物理', '材料化学', '数字经济', '金融科技', '智能医学工程', '新能源科学与工程', '生物技术', '智能医学工程（脑机接口特色班）', '新能源科学与工程（数智能源特色班）', '材料化学（新材料特色班）', '生物技术（生物智造特色班）', '智能科学与技术（具身与行为智能特色班）']

def _explicit_majors(raw):
    # Intent is captured only in an explicit optional line, never inferred from
    # a mention such as "不想学计算机科学与技术" in the reflection.
    match = re.search(r'(?:^|\n)\s*想了解[:：]([^\n]+)', raw)
    if not match:
        return []
    values = [x.strip().strip('。') for x in re.split(r'[,，、;；]+',match.group(1)) if x.strip()]
    if len(values)>30 or any(len(x)>100 for x in values):
        raise ValueError('想了解的专业请填最多30个完整名称')
    return list(dict.fromkeys(values))

def handler(params):
    try:
        params = copy.deepcopy(params)
        op = params.get('op')
        if op == 'reflect_auto_majors':
            params['op']='reflect'
            params['majors']=_explicit_majors(params.get('user_text',''))
        elif op == 'confirm_record':
            raw = params.get('user_text','')
            if raw.startswith('更正并确认：') or raw.startswith('更正并确认:'):
                state = loads(params['state_json'])
                state['requested_majors'] = _explicit_majors(re.split('[:：]',raw,maxsplit=1)[1])
                params['state_json'] = dumps(state)
        return _core_handler(params)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError) as error:
        return {'ok':False,'action':'error','state_json':params.get('state_json','') if isinstance(params,dict) else '',
                'prompt':'','preview':'','feedback':str(error),'result_json':'','report':'','error':str(error)}


"""Appended to the embedded engine. All menu selections arrive as branch constants."""
_legacy_platform_handler = handler

SELECTION_VERSION = '4.0.0'

SELECTION_ROADMAP = "**这次会怎么进行**\n\n先选一个小情境，试试你的做法；如果愿意，再看看条件改变后会怎样。最后由你决定是否整理一份可核对的探索记录——整理前我会明确问你，并给你留想法的入口。\n\n*不用做满全程。你可以随时结束；不会把活动当成能力或专业适配测评。*"


def _reported_group(raw):
    text = clean_text(raw, 600).strip().rstrip("。！! ")
    if not text:
        return None
    if text in {"不清楚", "不知道", "暂不提供", "还没确定"}:
        return "unknown"
    aliases = {}
    for gid, group in CATALOG['groups'].items():
        values = [group['display_name']]
        if not gid.startswith('boqin_'):
            values.append(group['name'])
        else:
            direction = '信息' if gid == 'boqin_info' else '理科'
            values.extend(['卓越拔尖计划伯芩班（'+direction+'方向）', '伯芩班（'+direction+'方向）', '伯芩班'+direction+'方向'])
        for name in values:
            aliases[name] = gid
            aliases[name.replace('伯芩', '伯苓')] = gid
    if text in aliases:
        return aliases[text]
    matches = set()
    # Read explicit membership clauses; an additional interest clause must not
    # invalidate an otherwise clear self-report or trigger another class question.
    for clause in re.split(r'[。！!？?；;，,\n]+',text):
        clause=clause.strip()
        if not clause or re.search(r"想去|想选|想学|希望|不是|不在|不属于|不确定|可能|如果|假如|[“”‘’\"]",clause):
            continue
        if clause in aliases:
            matches.add(aliases[clause])
        for alias, gid in sorted(aliases.items(), key=lambda pair: -len(pair[0])):
            pattern = r"(?:我(?:现在|目前)?(?:是|在|属于|就读于)|我(?:现在|目前)?的(?:专业)?(?:当前|所属)?大类是|目前(?:是|在|属于))\s*" + re.escape(alias) + r"(?:大类)?(?:的(?:学生)?|学生)?"
            if re.fullmatch(pattern,clause):
                matches.add(gid)
    return next(iter(matches)) if len(matches)==1 else None


def _selection(params):
    selection = loads(params.get('selection_json', ''))
    if selection.get('version') != SELECTION_VERSION:
        raise ValueError('selection version mismatch')
    if selection.get('group_id') not in set(CATALOG['groups']) | {'unknown'}:
        raise ValueError('unknown group')
    return selection


def _families_for(group_id):
    if group_id in GROUP_FAMILIES:
        return list(GROUP_FAMILIES[group_id])
    return list(DEFAULT_MENU_FAMILIES)


def _relevance_rank(case, group_id):
    if group_id in (None, 'unknown') or group_id not in CATALOG['groups']:
        return 1
    own = set(CATALOG['groups'][group_id].get('majors', []))
    return 0 if (own & set(case.get('related_majors', []))) else 1


def _menu_result(selection):
    task = selection['task_id']
    if task == 'auto':
        selection['families_shown'] = _families_for(selection['group_id'])
        return dict(ok=True, action='need_activity', group_id=selection['group_id'], selection_json=dumps(selection),
                    prompt="## 想从哪种小问题开始？\n\n选择一项你愿意动手想一想的事情。不需要有基础，也不用把它当成选专业的决定。")
    if task not in BANK['families']:
        raise ValueError('unknown activity')
    cases = [case for case in BANK['cases'].values() if case['task_id'] == task]
    if len(cases) != 3:
        raise ValueError('case count must be three')
    cases = sorted(cases, key=lambda c: _relevance_rank(c, selection['group_id']))
    selection['case_ids'] = [case['case_id'] for case in cases]
    related = sum(1 for case in cases if _relevance_rank(case, selection['group_id']) == 0)
    if selection['group_id'] == 'unknown':
        note = ""
    elif related:
        note = "前 %d 个与你的大类直接相关。" % related
    else:
        note = "这三个情境离你的大类稍远，可以当作跨界了解。"
    return dict(ok=True, action='menu', group_id=selection['group_id'], selection_json=dumps(selection),
                prompt="## 选一个更想试试的情境\n\n这三个情境练习同一类方法，但问题和条件不同。点一个你更想了解的就好，也可以让系统替你随机挑一个。" + note + "\n\n*题目使用编写的教学数据，每次打开细节可能略有不同；不是真实校内考题。*",
                **{'case'+str(index+1):case['title'] for index,case in enumerate(cases)})


def _roll_seed(selection, extra):
    base = selection.get('session_seed') or selection.get('group_id', 'unknown')
    return '|'.join([str(base), str(extra), str(selection.get('rolls', 0))])


def _selection_finish(params):
    selection = _selection(params)
    group = CATALOG['groups'].get(selection['group_id'], {}).get('display_name', '尚未提供')
    text = "# 本次探索记录\n\n**所属大类：** " + markdown_text(group) + "\n\n这次先到这里。还没有开始具体情境，也没有确认或试算方案，因此没有计算结果。\n\n*没有根据选择或退出推断你的能力、兴趣或专业适合程度。下次想体验时，可以重新开始。*"
    return dict(ok=True, action='stopped', selection_json=dumps(selection), report=text, display_text=text)


def _record_summary(state):
    case = case_of(state)
    count = sum(event.get('kind') == 'evaluated' for event in state['events'])
    parts = ["## 最后，核对一下想留下的记录", "**体验内容：** " + case['title'],
             "你已经确认并试过 **" + str(count) + " 个方案**。结果会原样放进最终记录。"]
    if state.get('reflection_raw'):
        parts += ["你对体验的感受：\n\n" + quoted(state['reflection_raw'])]
    else:
        parts += ["你暂时没有填写感受，这部分会如实留空。"]
    if state.get('requested_majors'):
        scope = scope_majors(state['group_id'], state['group_confirmed'], state['requested_majors'])
        for field, label in [('within_group','按你提供的大类清单属于类内'), ('cross_group','跨大类兴趣，转入资格尚未核验'), ('unverified','范围尚待核验')]:
            if scope[field]:
                parts.append('**'+label+'：** '+'、'.join(markdown_text(x) for x in scope[field]))
    parts += ["感受准确的话，选择‘记录准确，完成体验’；也可以改一下，或先不确认、保留这份记录。"]
    return '\n\n'.join(parts)


def _v4_dispatch(params):
    params = copy.deepcopy(params)
    op = params.get('op')
    if op == 'init_selection':
        raw = params.get('reported_group_text', '')
        gid = _reported_group(raw)
        task = ALIASES.get(params.get('task_id'), params.get('task_id')) or 'auto'
        if task not in set(BANK['families']) | {'auto'}:
            task = 'auto'
        seed_text = clean_text(params.get('session_seed', '') or '', 80)
        excluded_raw = clean_text(params.get('exclude_case_ids', '') or '', 2000)
        excluded = [x.strip() for x in re.split(r'[,，;；\s]+', excluded_raw) if x.strip() in BANK['cases']][:40]
        selection = dict(version=SELECTION_VERSION, task_id=task, group_id=gid or 'unknown',
                         group_confirmed=gid not in (None, 'unknown'), group_raw=raw if gid is not None else '',
                         session_seed=seed_text, exclude_case_ids=excluded, rolls=0)
        if gid is not None:
            group = CATALOG['groups'].get(gid, {}).get('display_name', '尚未确定')
            intro = SELECTION_ROADMAP + '\n\n**这次使用的大类信息：** ' + markdown_text(group) + '。'
        else:
            intro = SELECTION_ROADMAP
        return dict(ok=True, action='known_group' if gid is not None else 'need_group',
                    selection_json=dumps(selection), prompt=intro, display_text=intro)
    if op == 'set_group':
        selection = _selection(params)
        gid = params.get('group_id')
        if gid not in set(CATALOG['groups']) | {'unknown'}:
            raise ValueError('unknown group')
        selection.update(group_id=gid, group_confirmed=gid != 'unknown', group_raw=CATALOG['groups'].get(gid,{}).get('display_name','暂不提供'))
        return dict(ok=True, action='known_group', selection_json=dumps(selection))
    if op in ('selection_finish', 'selection_other'):
        return _selection_finish(params)
    if op in ('prepare_cases', 'set_activity'):
        selection = _selection(params)
        if op == 'set_activity':
            task = params.get('task_id')
            if task == 'random':
                families = _families_for(selection['group_id'])
                families = [f for f in families if any(c['case_id'] not in selection.get('exclude_case_ids', []) for c in BANK['cases'].values() if c['task_id'] == f)] or families
                roll = int(hashlib.sha256(_roll_seed(selection, 'activity').encode('utf-8')).hexdigest(), 16)
                task = families[roll % len(families)]
                selection['rolls'] = selection.get('rolls', 0) + 1
            if task not in BANK['families']:
                raise ValueError('unknown activity')
            selection['task_id'] = task
        return _menu_result(selection)
    if op == 'select_case' and 'case_index' in params:
        selection = _selection(params)
        index = params['case_index']
        if type(index) is not int or index not in (-1, 0, 1, 2):
            raise ValueError('invalid case branch')
        ids = selection['case_ids']
        if index == -1:
            roll = int(hashlib.sha256(_roll_seed(selection, 'case').encode('utf-8')).hexdigest(), 16)
            index = roll % len(ids)
            selection['rolls'] = selection.get('rolls', 0) + 1
        result = _core_handler(dict(op='start', task_id=selection['task_id'], case_id=ids[index],
                                    group_id=selection['group_id'], group_confirmed=selection['group_confirmed'],
                                    cohort='未提供', seed=_roll_seed(selection, ids[index]),
                                    exclude_case_ids=selection.get('exclude_case_ids', [])))
        if result['ok']:
            state = loads(result['state_json'])
            state['group_raw'] = selection.get('group_raw', '')
            state['group_source'] = 'user_self_report_not_officially_verified'
            result['state_json'] = dumps(state)
        return result
    if op == 'submit_button':
        state = loads(params['state_json'])
        case = case_of(state)
        choice = params.get('choice')
        if _mode_of(case, state) != 'choice' or choice not in ('A', 'B', 'C'):
            raise ValueError('invalid proposal branch')
        raw = _rendered_options(case, state['phase'], state)[choice]
        return _core_handler(dict(op='propose', state_json=dumps(state), user_text=raw,
                                  candidate_json=dumps(dict(action='submit', plan={'choice':choice,'reason':''}, quote=raw, question=''))))
    if op == 'reflect_auto_majors':
        state = loads(params['state_json'])
        raw = params.get('user_text', '')
        params['op'] = 'reflect'
        # An absent optional line must not erase a previously stated intention.
        params['majors'] = _explicit_majors(raw) if re.search(r'(?:^|\n)\s*想了解[:：]', raw) else state.get('requested_majors', [])
        return _core_handler(params)
    if op == 'confirm_record':
        raw = params.get('user_text', '')
        if raw.startswith(('更正并确认：','更正并确认:')):
            state = loads(params['state_json'])
            if re.search(r'(?:^|\n)\s*想了解[:：]', re.split('[:：]',raw,maxsplit=1)[1]):
                state['requested_majors'] = _explicit_majors(re.split('[:：]',raw,maxsplit=1)[1])
                params['state_json'] = dumps(state)
        return _core_handler(params)
    return _legacy_platform_handler(params)


def handler(params):
    try:
        result = _v4_dispatch(params)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        if isinstance(params, dict) and params.get('state_json'):
            result = _core_handler(dict(op='invalid_recoverable_operation', state_json=params['state_json']))
        else:
            text = '## 这次还没有开始具体情境\n\n刚才的选择没有成功接上，因此没有生成新的计算结果。你可以重新开始一次；这一步不会被记录成做题结果。'
            result = dict(ok=False, action='error', display_text=text, report=text, feedback=text, error=str(exc))
    if result.get('state_json'):
        try:
            state = loads(result['state_json'])
            case = case_of(state)
            result['mode'] = _mode_of(case, state)
            result['group_id'] = state.get('group_id', '')
            if not result.get('reflection_prompt'):
                result['reflection_prompt'] = case['reflection']
            if result['mode'] == 'choice':
                rendered = _rendered_options(case, state['phase'], state)
                for choice in ('A','B','C'):
                    result['choice'+choice] = rendered[choice]
            result['record_summary'] = _record_summary(state)
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            pass
    notice = params.get('finish_notice', '') if isinstance(params, dict) else ''
    if notice and (result.get('report') or result.get('feedback')):
        result['display_text'] = '*'+markdown_text(notice)+'*\n\n'+result.get('display_text',result.get('report',''))
        if result.get('feedback'):
            result['feedback'] = '*'+markdown_text(notice)+'*\n\n'+result['feedback']
    names = ['action','state_json','prompt','preview','feedback','result_json','report','error','case_id','task_id',
             'normalizer_context','knowledge_query','catalog_json','scope_json','reflection_prompt','selection_json',
             'display_text','mode','group_id','case1','case2','case3','choiceA','choiceB','choiceC','record_summary']
    normalized = {name:result.get(name,'') for name in names}
    normalized['ok'] = result.get('ok',False)
    return normalized

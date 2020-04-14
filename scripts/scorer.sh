A=6
B=12
C=3
D=0

PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/prod/formula18_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --prod --scores-collection scores-f18-A-"$A"-B-"$B"-C-"$C"-D-"$D"

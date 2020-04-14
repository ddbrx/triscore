A=6
B=13
C=1
D=1

PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/prod/formula8_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --prod --scores-collection scores-f8-A-"$A"-B-"$B"-C-"$C"-D-"$D"

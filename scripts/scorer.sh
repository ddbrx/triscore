A=10
B=104
C=5
D=2

PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/prod/formula5_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --prod --scores-collection scores-f6-A-"$A"-B-"$B"-C-"$C"-D-"$D"

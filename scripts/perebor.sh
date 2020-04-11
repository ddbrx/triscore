A=16
B=20
C=3
D=3

PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/manual/no_first_time_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt

# SCORES="scores-A-$A-B-$B-C-$C-D-$D"
# PYTHONPATH=./ python3 score/elo_scorer.py --log-file .tmp/prod/log_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --scores-collection $SCORES --prod

# C=2
# D=1

# for B in {20..20}; do
# 	for A in {10..20..2}; do
# 		# if (( A < B / 5 )); then
# 		# 	continue
# 		# fi

# 		# if (( A > B / 2 )); then
# 		# 	continue
# 		# fi


# 		echo "B: $B A: $A"
# 		PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/perebor_formula3/elo_log_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt
# 	done
# done

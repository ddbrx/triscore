# A=10
# B=104
# C=5
# D=2

# PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/manual/formula6_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt

# SCORES="scores-A-$A-B-$B-C-$C-D-$D"
# PYTHONPATH=./ python3 score/elo_scorer.py --log-file .tmp/prod/log_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --scores-collection $SCORES --prod

D=2

for B in {105..101}; do
	for A in {10..2..2}; do
        for C in {10..2..2}; do
            # if (( A < B / 5 )); then
            # 	continue
            # fi

            # if (( A > B / 2 )); then
            # 	continue
            # fi

            echo "B: $B A: $A C: $C"
            PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/perebor_formula6/A_"$A"_B_"$B"_C_"$C"_D_"$D".txt
        done
	done
done

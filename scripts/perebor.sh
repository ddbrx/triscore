# A=10
# B=104
# C=5
# D=2

# PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/manual/formula6_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt

# SCORES="scores-A-$A-B-$B-C-$C-D-$D"
# PYTHONPATH=./ python3 score/elo_scorer.py --log-file .tmp/prod/log_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --scores-collection $SCORES --prod

for B in {12..12}; do
    for A in {6..6..1}; do
        for C in {3..3..1}; do
            for D in {0..0}; do
                # if (( A < B / 5 )); then
                # 	continue
                # fi

                # if (( A > B / 2 )); then
                # 	continue
                # fi

                echo "B: $B A: $A C: $C D:$D"
                PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --log-file .tmp/perebor_formula18/A_"$A"_B_"$B"_C_"$C"_D_"$D".txt
            done
        done
    done
done

# formula 9
# for D in {1..2}; do
# if (( A < B / 5 )); then
# 	continue
# fi

# if (( A > B / 2 )); then
# 	continue
# fi

# echo "D:$D"
# PYTHONPATH=./ python3 score/elo_scorer.py --D=$D --log-file .tmp/perebor_formula10/D_"$D".txt
# done

# PYTHONPATH=./ python3 score/elo_scorer.py --file .tmp/elo_log.txt --prod
A=3
B=16
for D in {1..2}; do
	for C in {1..2}; do
		SCORES="scores-C-$C-D-$D"
		PYTHONPATH=./ python3 score/elo_scorer.py --A=$A --B=$B --C=$C --D=$D --file .tmp/perebor/elo_log_A_"$A"_B_"$B"_C_"$C"_D_"$D".txt --scores-collection="$SCORES" --prod
	done
done

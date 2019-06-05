echo Fidelity Test Example

cd ../eval-scripts

python3 ./scripts/run-fidelity-exp.py --outdir ../cs244_final_project/fidelity --scenario drop --ipcs netlink --duration 5 --iters 1 --alg cubic

cd ../cs244_final_project

python src/plot_cwnd_hist.py --indir ./fidelity --outdir .




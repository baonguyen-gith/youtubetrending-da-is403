"""Usage: python run_all.py --data-dir ../../02_Data/data_final --output-dir ../../04_Outputs/data_final"""
import argparse
from analysis_common import get_data,make_H
import prep,q2a_tests,q2b_anova,q3a_regression

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',required=True);ap.add_argument('--output-dir',required=True)
    args=ap.parse_args()
    data=get_data(args.data_dir)
    h=prep.run(args.data_dir,args.output_dir)
    q2a_tests.run(h,args.output_dir)
    q2b_anova.run(h,args.output_dir)
    q3a_regression.run(h,args.output_dir)
if __name__=='__main__':main()

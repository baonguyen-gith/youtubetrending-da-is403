script_file <- grep('^--file=', commandArgs(FALSE), value=TRUE)
SCRIPT_DIR <- if (length(script_file)) dirname(normalizePath(sub('^--file=', '', script_file[1]))) else getwd()
# Run the full Kien pipeline; all output suffixes _R prevent overwriting Python files.
here<-SCRIPT_DIR
source(file.path(here,'prep.R'))
source(file.path(here,'q2a_tests.R'))
source(file.path(here,'q2b_anova.R'))
source(file.path(here,'q3a_regression.R'))
a<-get_args()
h<-prep_run(a$data_dir,a$output_dir)
q2a_run(h,a$output_dir)
q2b_run(h,a$output_dir)
q3a_run(h,a$output_dir)
message('R pipeline complete')

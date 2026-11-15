packages <- c('data.table','car','rstatix','sandwich','lmtest','effectsize')
needed <- packages[!vapply(packages,requireNamespace,logical(1),quietly=TRUE)]
if(length(needed)) install.packages(needed,repos='https://cloud.r-project.org')
cat('Available:',paste(packages[vapply(packages,requireNamespace,logical(1),quietly=TRUE)],collapse=', '),'\n')

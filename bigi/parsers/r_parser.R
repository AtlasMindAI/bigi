if (!requireNamespace("jsonlite", quietly = TRUE)) {
  cat(paste("Error: The R package 'jsonlite' is required by BiGI to parse R scripts, but it is not installed.\n",
            "Please install it using: install.packages('jsonlite') within your R console.\n"),
      file = stderr())
  quit(status = 1)
}
library(jsonlite)

# Helper function to get text representation of a sub-tree node in getParseData
get_text <- function(df, id) {
  if (is.null(id) || is.na(id) || length(id) == 0) return("")
  descendants <- function(node_id) {
    if (is.null(node_id) || is.na(node_id) || length(node_id) == 0) return(NULL)
    children <- df$id[which(df$parent == node_id)]
    if (length(children) == 0) return(node_id)
    return(c(node_id, unlist(lapply(children, descendants))))
  }
  all_ids <- descendants(id)
  if (length(all_ids) == 0) return("")
  terminals <- df[which(df$id %in% all_ids & df$terminal == TRUE), ]
  if (nrow(terminals) == 0) return("")
  terminals <- terminals[order(terminals$line1, terminals$col1), ]
  paste(terminals$text, collapse="")
}

# Helper to reconstruct package qualified names like pkg::func
get_qualified_name <- function(df, id, text) {
  if (is.null(id) || is.na(id) || length(id) == 0) return(text)
  parent_id <- df$parent[which(df$id == id)]
  if (length(parent_id) > 0 && !is.na(parent_id) && parent_id > 0) {
    siblings <- df[which(df$parent == parent_id), ]
    ns_get <- siblings[which(siblings$token == "NS_GET"), ]
    if (nrow(ns_get) > 0) {
      siblings <- siblings[order(siblings$line1, siblings$col1), ]
      return(paste(siblings$text, collapse=""))
    }
  }
  return(text)
}

# Parse a single R file
parse_r_file <- function(file_path, base_dir = "") {
  rel_path <- file_path
  if (nchar(base_dir) > 0) {
    base_dir_norm <- gsub("/+$", "", normalizePath(base_dir, mustWork = FALSE))
    file_path_norm <- normalizePath(file_path, mustWork = FALSE)
    if (startsWith(file_path_norm, base_dir_norm)) {
      rel_path <- substring(file_path_norm, nchar(base_dir_norm) + 1)
      rel_path <- gsub("^/+", "", rel_path)
    }
  }
  
  res <- list(definitions = list(), calls = list())
  
  tryCatch({
    p <- tryCatch({
      parse(file_path, keep.source = TRUE)
    }, error = function(e) {
      warning(paste("Failed to parse", file_path, ":", e$message))
      return(NULL)
    })
    
    if (is.null(p)) return(res)
    
    df <- getParseData(p)
    if (is.null(df) || nrow(df) == 0) return(res)
    
    # 1. Extract function definitions
    func_rows <- df[which(df$token == "FUNCTION"), ]
    defs <- list()
    
    if (nrow(func_rows) > 0) {
      for (i in seq_len(nrow(func_rows))) {
        f_row <- func_rows[i, ]
        f_id <- f_row$parent  # The FUNCTION expression node
        f_expr_row <- df[which(df$id == f_id), ]
        
        # Look for assignment of this expression
        gp_id <- df$parent[which(df$id == f_id)]
        if (length(gp_id) > 0 && !is.na(gp_id) && gp_id > 0) {
          gp_children <- df[which(df$parent == gp_id), ]
          assign_op <- gp_children[which(gp_children$token %in% c("LEFT_ASSIGN", "EQ_ASSIGN", "RIGHT_ASSIGN")), ]
          
          if (nrow(assign_op) > 0) {
            op <- assign_op$token[1]
            
            if (op %in% c("LEFT_ASSIGN", "EQ_ASSIGN")) {
              lhs_expr <- gp_children[which(gp_children$id != f_id & gp_children$id != assign_op$id[1]), ]
              if (nrow(lhs_expr) > 0 && !is.na(lhs_expr$id[1])) {
                func_name <- get_text(df, lhs_expr$id[1])
                if (nchar(func_name) > 0) {
                  defs[[length(defs) + 1]] <- list(
                    name = func_name,
                    file = rel_path,
                    line1 = f_expr_row$line1,
                    col1 = f_expr_row$col1,
                    line2 = f_expr_row$line2,
                    col2 = f_expr_row$col2
                  )
                }
              }
            } else if (op == "RIGHT_ASSIGN") {
              rhs_expr <- gp_children[which(gp_children$id != f_id & gp_children$id != assign_op$id[1]), ]
              if (nrow(rhs_expr) > 0 && !is.na(rhs_expr$id[1])) {
                func_name <- get_text(df, rhs_expr$id[1])
                if (nchar(func_name) > 0) {
                  defs[[length(defs) + 1]] <- list(
                    name = func_name,
                    file = rel_path,
                    line1 = f_expr_row$line1,
                    col1 = f_expr_row$col1,
                    line2 = f_expr_row$line2,
                    col2 = f_expr_row$col2
                  )
                }
              }
            }
          }
        }
      }
    }
    
    # 2. Extract function calls
    call_rows <- df[which(df$token == "SYMBOL_FUNCTION_CALL"), ]
    calls <- list()
    
    if (nrow(call_rows) > 0) {
      for (i in seq_len(nrow(call_rows))) {
        c_row <- call_rows[i, ]
        call_name <- get_qualified_name(df, c_row$id, c_row$text)
        
        # Determine caller (enclosing function)
        caller_name <- NA
        best_span <- Inf
        
        if (length(defs) > 0) {
          for (d in defs) {
            # Check if call is within d's range
            is_inside <- FALSE
            
            # Simplified range checking:
            if (d$line1 < c_row$line1 && c_row$line1 < d$line2) {
              is_inside <- TRUE
            } else if (d$line1 == c_row$line1 && d$line2 == c_row$line2) {
              if (d$col1 <= c_row$col1 && c_row$col2 <= d$col2) {
                is_inside <- TRUE
              }
            } else if (d$line1 == c_row$line1 && c_row$line1 < d$line2) {
              if (d$col1 <= c_row$col1) {
                is_inside <- TRUE
              }
            } else if (d$line2 == c_row$line2 && d$line1 < c_row$line2) {
              if (c_row$col2 <= d$col2) {
                is_inside <- TRUE
              }
            }
            
            if (is_inside) {
              span <- d$line2 - d$line1
              if (span < best_span) {
                best_span <- span
                caller_name <- d$name
              }
            }
          }
        }
        
        calls[[length(calls) + 1]] <- list(
          name = call_name,
          file = rel_path,
          line1 = c_row$line1,
          col1 = c_row$col1,
          line2 = c_row$line2,
          col2 = c_row$col2,
          caller = if (is.na(caller_name)) "" else caller_name
        )
      }
    }
    
    res$definitions <- defs
    res$calls <- calls
  }, error = function(e) {
    warning(paste("Error processing R file", file_path, ":", e$message))
  })
  
  return(res)
}

# Main execution
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  cat(toJSON(list(definitions = list(), calls = list()), auto_unbox = TRUE))
  q()
}

target <- args[1]
all_defs <- list()
all_calls <- list()

if (grepl("\\.json$", target, ignore.case = TRUE)) {
  r_files <- fromJSON(target)
  base_dir <- args[2]
  for (f in r_files) {
    res <- parse_r_file(f, base_dir = base_dir)
    all_defs <- c(all_defs, res$definitions)
    all_calls <- c(all_calls, res$calls)
  }
} else if (dir.exists(target)) {
  # Scan directory for R files recursively
  r_files <- list.files(target, pattern = "\\.[rR]$", recursive = TRUE, full.names = TRUE)
  for (f in r_files) {
    res <- parse_r_file(f, base_dir = target)
    all_defs <- c(all_defs, res$definitions)
    all_calls <- c(all_calls, res$calls)
  }
} else if (file.exists(target)) {
  res <- parse_r_file(target, base_dir = dirname(target))
  all_defs <- res$definitions
  all_calls <- res$calls
}

output <- list(
  definitions = all_defs,
  calls = all_calls
)

cat(toJSON(output, auto_unbox = TRUE, pretty = TRUE))

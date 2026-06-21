library(jsonlite)

# Helper function to get text representation of a sub-tree node in getParseData
get_text <- function(df, id) {
  descendants <- function(node_id) {
    children <- df$id[df$parent == node_id]
    if (length(children) == 0) return(node_id)
    return(c(node_id, unlist(lapply(children, descendants))))
  }
  all_ids <- descendants(id)
  terminals <- df[df$id %in% all_ids & df$terminal == TRUE, ]
  terminals <- terminals[order(terminals$line1, terminals$col1), ]
  paste(terminals$text, collapse="")
}

# Helper to reconstruct package qualified names like pkg::func
get_qualified_name <- function(df, id, text) {
  parent_id <- df$parent[df$id == id]
  if (length(parent_id) > 0 && parent_id > 0) {
    siblings <- df[df$parent == parent_id, ]
    ns_get <- siblings[siblings$token == "NS_GET", ]
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
    rel_path <- gsub(paste0("^", reindent_path(base_dir), "/?"), "", file_path)
  }
  
  res <- list(definitions = list(), calls = list())
  
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
  func_rows <- df[df$token == "FUNCTION", ]
  defs <- list()
  
  if (nrow(func_rows) > 0) {
    for (i in seq_len(nrow(func_rows))) {
      f_row <- func_rows[i, ]
      f_id <- f_row$parent  # The FUNCTION expression node
      f_expr_row <- df[df$id == f_id, ]
      
      # Look for assignment of this expression
      gp_id <- df$parent[df$id == f_id]
      if (length(gp_id) > 0 && gp_id > 0) {
        gp_children <- df[df$parent == gp_id, ]
        assign_op <- gp_children[gp_children$token %in% c("LEFT_ASSIGN", "EQ_ASSIGN", "RIGHT_ASSIGN"), ]
        
        if (nrow(assign_op) > 0) {
          op <- assign_op$token[1]
          symbol_node <- NULL
          
          if (op %in% c("LEFT_ASSIGN", "EQ_ASSIGN")) {
            lhs_expr <- gp_children[gp_children$id != f_id & gp_children$id != assign_op$id[1], ]
            if (nrow(lhs_expr) > 0) {
              # Concatenate text of LHS to handle namespaces, objects, lists, etc.
              func_name <- get_text(df, lhs_expr$id[1])
              defs[[length(defs) + 1]] <- list(
                name = func_name,
                file = rel_path,
                line1 = f_expr_row$line1,
                col1 = f_expr_row$col1,
                line2 = f_expr_row$line2,
                col2 = f_expr_row$col2
              )
            }
          } else if (op == "RIGHT_ASSIGN") {
            # Symbol is on the right
            rhs_expr <- gp_children[gp_children$id != f_id & gp_children$id != assign_op$id[1], ]
            if (nrow(rhs_expr) > 0) {
              func_name <- get_text(df, rhs_expr$id[1])
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
  
  # 2. Extract function calls
  call_rows <- df[df$token == "SYMBOL_FUNCTION_CALL", ]
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
  return(res)
}

reindent_path <- function(path) {
  # Normalize trailing slash
  gsub("/+$", "", path)
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

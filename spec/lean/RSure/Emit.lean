import RSure.Basic

def main : IO Unit := do
  IO.println s!"share_zero|0|{RSure.share 0 0}"
  IO.println s!"share_half|1000,5000|{RSure.share 1000 5000}"

#eval main

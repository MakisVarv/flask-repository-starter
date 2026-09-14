def apply_sorting(
    statement,
    sort_columns,
    sort_field,
    descending,
    secondary_column,
):

    sort_column = sort_columns[sort_field]
    order = sort_column.desc() if descending else sort_column.asc()
    if sort_field == "id":
        statement = statement.order_by(order)
    else:
        statement = statement.order_by(order, secondary_column.asc())

    return statement

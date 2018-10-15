def query_netbox(req, url, params, secure=True, batch_size=500):

    offset = 0
    keep_querying = True

    results = {"count": 0, "results": []}

    while keep_querying:

        paging_params = "offset=%s&limit=%s" % (offset, batch_size)
        api_url_params = paging_params + "&" + params

        resp = req.get(url, params=api_url_params, verify=secure)

        resp.raise_for_status()
        resp_dict = resp.json()

        # TODO check for response code
        results["count"] = resp_dict["count"]
        results["results"].extend(resp_dict["results"])

        offset += batch_size
        if int(resp_dict["count"]) < offset:
            keep_querying = False

    return results

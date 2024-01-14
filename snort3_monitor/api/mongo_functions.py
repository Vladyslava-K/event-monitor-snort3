from mongo.db_config import perf_monitor


def pgc_report(start, end):
    """
    Retrieve performance monitoring data within the specified time range.

    Parameters:
    - start (datetime): Start timestamp for the query range.
    - end (datetime): End timestamp for the query range.

    Returns:
    - list: A list of documents containing performance monitoring data within the specified time range.
    """
    result = []
    with perf_monitor.find({'timestamp': {'$gte': start, '$lte': end}}) as cursor:
        for document in cursor:
            result.append(document)

    return result


def pgc_module_report(start, end, module):
    """
    Retrieve performance monitoring data for a specific module within the specified time range.

    Parameters:
    - start (datetime): Start timestamp for the query range.
    - end (datetime): End timestamp for the query range.
    - module (str): The module for which performance data is requested.

    Returns:
    - dict: A dictionary containing performance data for the specified module within the time range.
    """
    result = {}
    with perf_monitor.find({'timestamp': {'$gte': start, '$lte': end}}) as cursor:
        for document in cursor:
            timestamp = document['timestamp']
            module_data = document.get(module)
            if not module_data:
                continue
            else:
                timestamp = str(timestamp)
                result[timestamp] = {}
            for metric, value in module_data.items():
                if metric not in result[timestamp]:
                    result[timestamp][metric] = value
                else:
                    result[timestamp][metric] += value
    return result


def pgc_aggr(start, end):
    """
    Aggregate performance monitoring data for all modules within the specified time range.

    Parameters:
    - start (datetime): Start timestamp for the query range.
    - end (datetime): End timestamp for the query range.

    Returns:
    - dict: A dictionary containing aggregated performance data for all modules within the time range.
    """
    result = {}
    with perf_monitor.find({'timestamp': {'$gte': start, '$lte': end}}) as cursor:
        for document in cursor:
            for module, metrics in document.items():
                if module in ['timestamp', '_id']:
                    continue
                if module not in result:
                    result[module] = {}
                for metric, value in metrics.items():
                    if metric not in result[module]:
                        result[module][metric] = value
                    else:
                        if 'max' in metric:
                            result[module][metric] = max(result[module][metric], value)
                        elif 'min' in metric:
                            result[module][metric] = min(result[module][metric], value)
                        else:
                            result[module][metric] += value
    return result


def pgc_module_aggr(start, end, module):
    """
    Aggregate performance monitoring data for a specific module within the specified time range.

    Parameters:
    - start (datetime): Start timestamp for the query range.
    - end (datetime): End timestamp for the query range.
    - module (str): The module for which performance data is requested.

    Returns:
    - dict: A dictionary containing aggregated performance data for the specified module within the time range.
    """
    result = {module: {}}
    with perf_monitor.find({'timestamp': {'$gte': start, '$lte': end}}) as cursor:
        for document in cursor:
            module_data = document.get(module)
            if not module_data:
                continue
            for metric, value in module_data.items():
                if metric not in result[module]:
                    result[module][metric] = value
                else:
                    if 'max' in metric:
                        result[module][metric] = max(result[module][metric], value)
                    elif 'min' in metric:
                        result[module][metric] = min(result[module][metric], value)
                    else:
                        result[module][metric] += value
    return result

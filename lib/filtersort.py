from flask import request

class FilterSort():

    def make_sort(self, somedict):
        args = request.args
        allowedsort = {k: v for k, v in args.items() if k in somedict.keys() and v in ['asc', 'desc']}
        result = [ getattr(somedict[k], v) for k, v in allowedsort.items() ]

        return result

    def make_filter(self, filterdict):
        args = request.args
        allowedfilter = { k: v for k, v in args.items() if v in filterdict }
        return [ filterdict[v]("%" + str(k) + "%") for k, v in allowedfilter.items() ]

    def generate_next_sort(self, somelist):
        args = request.args
        allowedsort = {k: v for k, v in args.items() if k in somelist and v in ['asc', 'desc']}
        restlist = {k: 'none' for k in somelist}
        orderlist = {'none': 'asc', 'asc': 'desc', 'desc': 'none'}
        return {k: orderlist[v] for k,v in {**restlist, **allowedsort}.items()}

    def generate_current_sort(self, somelist):
        args = request.args
        allowedsort = {k: v for k, v in args.items() if k in somelist and v in ['asc', 'desc']}
        restlist = {k: 'none' for k in somelist}
        return {**restlist, **allowedsort}

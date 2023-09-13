import json
from odoo import http
from odoo.http import request, Response
from redis import Redis
import logging
_logger = logging.getLogger(__name__)

class TestRedis(http.Controller):
    
    # @http.route(["/api/test/partner/<int:partner_id>"], auth="public", methods=["GET"])
    # def GetPartnerData(self, partner_id=0):
    #     partner_id = request.env['res.partner'].sudo().browse(partner_id)
    #     result = {
    #         'name': partner_id.name,
    #         'mobile': partner_id.mobile,
    #         'email': partner_id.email
    #     }
    #     return Response(json.dumps(result), headers={"Content-Type": "application/json"})

    @http.route(["/api/test/partner/<int:partner_id>"], auth="public", methods=["GET"])
    def GetPartnerData(self, partner_id=0):
        result = {}
        is_from_redis = False
        try:
            Client = Redis(
                host="redis",
                port=6379
            )
            
            # set key_store format to redis
            key_store = "partner_id:%s" % (partner_id)
            # get data from redis by key_store
            redis_value = Client.get(key_store)
            # check if there are data's from redis by key_store
            # if data exist use data redis,
            # if not we will get the data from odoo database by Odoo ORM,
            # then insert the data to redis
            if redis_value:
                # json loads and decode the value from utf-8
                result = json.loads(redis_value.decode("utf-8"))
                # set flag field data from redis to be 'True'
                is_from_redis = True
            else:
                # get data from odoo database by ORM
                result = self.get_partner_data(partner_id)
                
                # insert into Redis
                if result:
                    # Insert Data to Redis w/ 30 Secs Expired Time                 
                    Client.set(key_store, json.dumps(result), ex=30)
                    # Add Log insert to Redis
                    _logger.info("CreateRedisPartnerData: %s, %s" % (key_store, result))
        except Exception as err:
            # get data from odoo database if failed to connect to redis server
            result = self.get_partner_data(partner_id)
        if result:
            result['is_from_redis'] = is_from_redis
        return Response(json.dumps(result), headers={"Content-Type": "application/json"})
    
    def get_partner_data(self, partner_id):
        data = {}
        partner = request.env['res.partner'].sudo().browse(partner_id)
        if partner:
            data = {
                'name': partner.name,
                'mobile': partner.mobile,
                'email': partner.email
            }
        return data
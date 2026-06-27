from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
import json

app = FastAPI()

# TEMP CART STORAGE
inprogress_orders = {}

print("SERVER STARTED")


@app.get("/")
async def home():

    return {
        "message": "Backend running"
    }


@app.post("/")
async def handle_request(request: Request):

    try:

        payload = await request.json()

        print("\n" + "="*60)
        print("NEW REQUEST")
        print("="*60)

        print(json.dumps(payload, indent=2))

        query_result = payload.get("queryResult")

        intent = query_result.get(
            "intent"
        ).get("displayName")

        parameters = query_result.get(
            "parameters", {}
        )

        output_contexts = query_result.get(
            "outputContexts", []
        )

        session_str = output_contexts[0]["name"]

        session_id = generic_helper.extract_session_id(
            session_str
        )

        print("INTENT:", intent)
        print("SESSION:", session_id)

        print("CURRENT CARTS:")
        print(inprogress_orders)

        intent_map = {

            "Order.Add": add_to_order,

            "Order.Edit": remove_from_order,

            "Order.Completion": complete_order,

            "Order.Status(Ongoing)": track_order
        }

        if intent not in intent_map:

            return JSONResponse(content={

                "fulfillmentText":
                f"Intent {intent} not recognized"
            })

        return intent_map[intent](
            parameters,
            session_id
        )

    except Exception as e:

        print("MAIN ERROR:", e)

        import traceback
        traceback.print_exc()

        return JSONResponse(content={

            "fulfillmentText":
            "Backend error"
        })


# ADD ITEMS
def add_to_order(parameters, session_id):

    try:

        food_items = parameters.get(
            "Food-Menu", []
        )

        quantities = parameters.get(
            "number", []
        )

        print("\nADD TO ORDER")
        print("ITEMS:", food_items)
        print("QUANTITIES:", quantities)

        # SINGLE VALUE FIX
        if not isinstance(food_items, list):

            food_items = [food_items]

        if not isinstance(quantities, list):

            quantities = [quantities]

        if not food_items:

            return JSONResponse(content={

                "fulfillmentText":
                "Please tell me what you'd like to order."
            })

        # DEFAULT QUANTITY
        if not quantities:

            quantities = [1] * len(food_items)

        # CREATE CART
        if session_id not in inprogress_orders:

            inprogress_orders[session_id] = {}

        cart = inprogress_orders[session_id]

        # ADD ITEMS TO CART
        for item, qty in zip(
            food_items,
            quantities
        ):

            item = str(item).strip()

            qty = int(qty)

            if item in cart:

                cart[item] += qty

            else:

                cart[item] = qty

        print("UPDATED CART:")
        print(cart)

        order_str = generic_helper.get_str_from_food_dict(
            cart
        )

        return JSONResponse(content={

            "fulfillmentText":
            f"Alright! So far your order is: "
            f"{order_str}. "
            f"Would you like anything else?"
        })

    except Exception as e:

        print("ADD ERROR:", e)

        import traceback
        traceback.print_exc()

        return JSONResponse(content={

            "fulfillmentText":
            "Error adding order"
        })
################################## EDIT ORDER
def remove_from_order(parameters, session_id):

    try:

        print("\nREMOVE FROM ORDER")

        food_items = parameters.get(
            "Food-Menu", []
        )

        quantities = parameters.get(
            "number", []
        )

        print("REMOVE ITEMS:", food_items)
        print("REMOVE QUANTITIES:", quantities)

        # CHECK ACTIVE CART
        if session_id not in inprogress_orders:

            return JSONResponse(content={

                "fulfillmentText":
                "Your cart is empty."
            })

        cart = inprogress_orders[session_id]

        # FIX SINGLE VALUES
        if not isinstance(food_items, list):

            food_items = [food_items]

        if not isinstance(quantities, list):

            quantities = [quantities]

        # DEFAULT REMOVE 1
        if not quantities:

            quantities = [1] * len(food_items)

        removed_items = []

        # REMOVE ITEMS
        for item, qty in zip(
            food_items,
            quantities
        ):

            item = str(item).strip()

            qty = int(qty)

            if item in cart:

                cart[item] -= qty

                removed_items.append(
                    f"{qty} {item}"
                )

                # REMOVE ITEM COMPLETELY
                if cart[item] <= 0:

                    del cart[item]

        print("UPDATED CART:")
        print(cart)

        # EMPTY CART
        if not cart:

            del inprogress_orders[session_id]

            return JSONResponse(content={

                "fulfillmentText":
                "All items removed. Your cart is now empty."
            })

        order_str = generic_helper.get_str_from_food_dict(
            cart
        )

        return JSONResponse(content={

            "fulfillmentText":
            f"Removed {', '.join(removed_items)}. "
            f"Your updated order is: {order_str}. "
            f"Would you like anything else?"
        })

    except Exception as e:

        print("REMOVE ERROR:", e)

        import traceback
        traceback.print_exc()

        return JSONResponse(content={

            "fulfillmentText":
            "Error removing item from order."
        })

# COMPLETE ORDER
def complete_order(parameters, session_id):

    try:

        print("\nCOMPLETE ORDER")
        print("SESSION:", session_id)

        if session_id not in inprogress_orders:

            return JSONResponse(content={

                "fulfillmentText":
                "Your cart is empty."
            })

        cart = inprogress_orders[session_id]

        print("FINAL CART:")
        print(cart)

        # RANDOM ORDER ID
        order_id = db_helper.generate_order_id()

        print("ORDER ID:", order_id)

        # INSERT ITEMS
        for item, qty in cart.items():

            print(
                f"Inserting {item} qty={qty}"
            )

            rcode = db_helper.insert_order_item(
                item,
                qty,
                order_id
            )

            if rcode == -1:

                return JSONResponse(content={

                    "fulfillmentText":
                    f"Failed saving {item}"
                })

        # INSERT TRACKING
        db_helper.insert_order_tracking(
            order_id,
            "in progress"
        )

        # GET TOTAL
        total = db_helper.get_total_order_price(
            order_id
        )
        # DELIVERY TIME ESTIMATION
        total_items = sum(cart.values())       
        delivery_time = 15 + (total_items * 5)

        # CLEAR CART
        del inprogress_orders[session_id]

        return JSONResponse(content={

            "fulfillmentText":
            f"Awesome! Your order has been placed successfully. "
            f"Your order id is #{order_id}. "
            f"Your total amount is ${total}."
            f"Estimated delivery time is {delivery_time} minutes."
        })

    except Exception as e:

        print("COMPLETE ERROR:", e)

        import traceback
        traceback.print_exc()

        return JSONResponse(content={

            "fulfillmentText":
            "Error completing order"
        })


##################################################### TRACK ORDER
def track_order(parameters, session_id):

    try:

        order_id = parameters.get("number")

        if not order_id:

            return JSONResponse(content={

                "fulfillmentText":
                "Please provide order id."
            })

        order_id = int(order_id)

        status = db_helper.get_order_status(
            order_id
        )

        if status:

            return JSONResponse(content={

                "fulfillmentText":
                f"Your order #{order_id} "
                f"is currently {status}."
            })

        return JSONResponse(content={

            "fulfillmentText":
            f"No order found with id {order_id}"
        })

    except Exception as e:

        print("TRACK ERROR:", e)

        import traceback
        traceback.print_exc()

        return JSONResponse(content={

            "fulfillmentText":
            "Error tracking order"
        })
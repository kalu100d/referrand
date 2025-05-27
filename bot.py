import telebot
import json
import os
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# 🔹 Replace with your bot token
TOKEN = "8041216769:AAHL-JfEz72jAt_jLQZ4KjxL3PulmDERfyg"
bot = telebot.TeleBot(TOKEN)

# 🔹 Channels (Users must join these to use the bot)
CHANNELS = ["@chanell22223", "@moneymakers_xd"]
ADMIN_ID = 6911602377  # Replace with your Telegram ID
ADMIN_CHANNEL = "@moneymakers_xd"  # Admin channel where the order message will be sent

# Data Storage
DATA_FILE = "data.json"
REFERRAL_CODE_FILE = "referralcode.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not os.path.exists(REFERRAL_CODE_FILE):
    with open(REFERRAL_CODE_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_referral_codes():
    with open(REFERRAL_CODE_FILE, "r") as f:
        return json.load(f)

def save_referral_codes(data):
    with open(REFERRAL_CODE_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
referral_codes = load_referral_codes()

def generate_referral_code():
    while True:
        code = str(random.randint(100000, 999999))  # Generate a 6-digit code
        if code not in referral_codes:
            return code

def check_joined(user_id):
    try:
        for channel in CHANNELS:
            chat_member = bot.get_chat_member(channel, user_id)
            if chat_member.status in ["left", "kicked"]:
                return False
        return True
    except:
        return False

def get_or_create_user(user_id, username):
    user_id = str(user_id)
    is_admin = (int(user_id) == ADMIN_ID)
    
    if user_id not in data:
        referral_code = generate_referral_code()
        data[user_id] = {
            "chat_id": user_id,
            "username": username,
            "points": 0,
            "wallet": "",
            "referrals": [],
            "joined": is_admin,  # Auto-join for admin
            "referral_code": referral_code,
            "referrer": None,
            "verified": is_admin,  # Auto-verify for admin
            "is_admin": is_admin  # Mark admin status
        }
        referral_codes[referral_code] = user_id  # Map referral code to user ID
        save_data(data)
        save_referral_codes(referral_codes)
    return data[user_id]

def handle_referral(user_id, referrer_id):
    user = data.get(str(user_id))
    if referrer_id and referrer_id in data:
        referrer = data[referrer_id]
        if user_id not in referrer['referrals']:
            referrer['referrals'].append(user_id)
            referrer['points'] += 1
            user['points'] += 1  # Award point to new user
            bot.send_message(referrer_id, f"🎉 You got 1 point! @{user['username']} joined using your referral code.")
            save_data(data)

def get_channel_buttons():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for channel in CHANNELS:
        keyboard.add(KeyboardButton(f"Join {channel}"))
    keyboard.add(KeyboardButton("✅ I have joined"))
    return keyboard

def get_menu_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("💰 My Balance"),
        KeyboardButton("👤 Referral"),
        KeyboardButton("🎁 Get Rewards"),
        KeyboardButton("📊 Statistics"),
        KeyboardButton("📞 Support")
    ]
    keyboard.add(*buttons)
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username or "NoUsername"
    user = get_or_create_user(user_id, username)

    # Auto-verify admin users without requiring referral code
    if user_id == ADMIN_ID and not user.get('verified', False):
        user['verified'] = True
        user['joined'] = True
        save_data(data)
        bot.send_message(user_id, "🔰 Admin detected! You've been automatically verified.")
        
    if not user.get('verified', False):
        welcome_text = "👋 Welcome to @getrewardsxd_bot!\n\n🔹 To access this bot, please enter a valid referral code.\n🔹 If you don't have one, ask a friend who is already using the bot.\n\n✏️ Send your referral code below:\n\n❗ Note: Without a referral code, you cannot proceed further."
        bot.send_message(user_id, welcome_text)
        bot.register_next_step_handler(message, process_referral_code)
    else:
        if not check_joined(user_id):
            bot.send_message(user_id, "🔐 Please join the required channels first!", reply_markup=get_channel_buttons())
        else:
            bot.send_message(user_id, "🚀 Welcome ! Choose an option:", reply_markup=get_menu_keyboard())

def process_referral_code(message):
    user_id = message.chat.id
    username = message.chat.username or "NoUsername"
    user = get_or_create_user(user_id, username)

    referrer_code = message.text.strip()
    if referrer_code in referral_codes:
        referrer_id = referral_codes[referrer_code]
        
        # Don't allow self-referral
        if str(referrer_id) == str(user_id):
            bot.send_message(user_id, "❌ You cannot use your own referral code. Please enter someone else's code.")
            bot.register_next_step_handler(message, process_referral_code)
            return
            
        # Add referrer to user data
        user['referrer'] = referrer_id
        user['verified'] = True
        user['joined'] = True
        
        # Handle referral points
        handle_referral(user_id, referrer_id)
        save_data(data)
        
        bot.send_message(user_id, "🎉 Thank you for verifying! You can now proceed to join our channels:", reply_markup=get_channel_buttons())
    else:
        bot.send_message(user_id, "❌ Invalid referral code. Please try again with a valid code.")
        bot.register_next_step_handler(message, process_referral_code)

@bot.message_handler(func=lambda message: message.text == "✅ I have joined")
def handle_joined(message):
    user_id = message.chat.id
    if check_joined(user_id):
        user = get_or_create_user(user_id, message.chat.username)
        if not user['joined']:
            user['joined'] = True
            save_data(data)
            handle_referral(user_id, None)  # No referrer if joined directly
        bot.send_message(user_id, "🎉 Thank you for joining! You can now start using the bot.", reply_markup=get_menu_keyboard())
    else:
        bot.send_message(user_id, "🔐 You need to join all the required channels before clicking 'I have joined'.", reply_markup=get_channel_buttons())

@bot.message_handler(func=lambda message: message.text == "💰 My Balance")
def balance(message):
    user = get_or_create_user(message.chat.id, message.chat.username)
    bot.send_message(message.chat.id, f"💰 Your Balance: {user['points']} Points")

@bot.message_handler(func=lambda message: message.text == "👤 Referral")
def referral(message):
    user_id = str(message.chat.id)
    user = get_or_create_user(user_id, message.chat.username)
    
    # Get user's referral code
    ref_code = user.get('referral_code', 'N/A')
    ref_count = len(user.get('referrals', []))
    
    # Create message with referral info and detailed instructions
    reply = f"Referral System 🎯\n\n"
    reply += f"🔹 Your Referral Code: `{ref_code}`\n"
    reply += f"➖ Share this code with your friends and earn rewards!\n"
    reply += f"👤 People referred: {ref_count}\n\n"
    
    reply += f"📌 How to Use the Bot?\n"
    reply += f"1️⃣ When a new user starts the bot, they must enter a referral code to continue.\n"
    reply += f"2️⃣ After entering the code, they will be asked to join both channels to unlock full access.\n"
    reply += f"3️⃣ Once they join the channels and click \"Joined,\" they can use the bot normally.\n"
    reply += f"4️⃣ For every successful referral, you will earn 1 point, which can be redeemed for amazing rewards!\n"
    reply += f"BOT: @{bot.get_me().username}\n\n"
    reply += f"⚡ Start inviting and earning now! 🚀"
    
    # Use HTML instead of Markdown to avoid parsing issues with special characters
    bot.send_message(user_id, reply, parse_mode="HTML")

@bot.message_handler(commands=['mycode'])
def my_referral_code(message):
    user_id = str(message.chat.id)
    user = get_or_create_user(user_id, message.chat.username)
    
    # Get user's referral code
    ref_code = user.get('referral_code', 'N/A') 
    
    reply = f"🔑 Your referral code: `{ref_code}`\n\n"
    reply += "Share this code with your friends to earn points!"
    
    bot.send_message(user_id, reply, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 Statistics")
def stats(message):
    bot.send_message(message.chat.id, f"📊 Total Users: {len(data)}")

@bot.message_handler(func=lambda message: message.text == "📞 Support")
def support(message):
    bot.send_message(message.chat.id, "📩 Send your support message:")
    bot.register_next_step_handler(message, send_support)

def send_support(message):
    bot.send_message(ADMIN_ID, f"📩 Support Request from {message.chat.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ Your request has been sent!")

@bot.message_handler(func=lambda message: message.text == "🎁 Get Rewards")
def get_rewards(message):
    user = get_or_create_user(message.chat.id, message.chat.username)
    if user['points'] < 3:
        bot.send_message(message.chat.id, "❌ You need at least 3 points to redeem a reward!")
        return

    # Create a well-formatted rewards menu
    rewards_menu = (
        "🎁 *Available Rewards* 🎁\n\n"
        "🔸 *3 Points Rewards:*\n"
        "  • 1️⃣ YouTube Premium (1 month) - Reply 'YT'\n"
        "  • 2️⃣ Crunchyroll Premium (1 month) - Reply 'CR'\n"
        "  • 3️⃣ JioSaavn Premium (1 month) - Reply 'JS1'\n\n"
        "🔸 *5 Points Rewards:*\n"
        "  • 4️⃣ Amazon Prime (1 month) - Reply 'AP'\n"
        "  • 5️⃣ JioSaavn Premium (1 year) - Reply 'JS12'\n\n"
        "✨ Simply reply with the code of your desired reward! ✨"
    )
    
    bot.send_message(message.chat.id, rewards_menu, parse_mode="Markdown")
    bot.register_next_step_handler(message, process_reward)

def process_reward(message):
    user = get_or_create_user(message.chat.id, message.chat.username)
    
    # Updated rewards dictionary with more options
    rewards = {
        "yt": (3, "YouTube Premium (1 month)"),
        "cr": (3, "Crunchyroll Premium (1 month)"),
        "js1": (3, "JioSaavn Premium (1 month)"),
        "ap": (5, "Amazon Prime (1 month)"),
        "js12": (5, "JioSaavn Premium (1 year)")
    }
    
    choice = message.text.lower().strip()

    if choice not in rewards:
        bot.send_message(message.chat.id, "❌ Invalid option. Please choose from the available rewards menu.")
        return

    cost, reward_name = rewards[choice]
    if user['points'] < cost:
        bot.send_message(message.chat.id, f"❌ Not enough points! You need {cost} points but have {user['points']}.")
        return

    # For YouTube Premium, request Gmail first
    if choice == "yt":
        bot.send_message(
            message.chat.id, 
            "📧 *Please provide a Gmail account* that has never been used for YouTube Premium before.\n\n"
            "Send your Gmail in this format: `/gmail youremail@gmail.com`\n\n"
            "❗ *Note:* Your Gmail must not have been used for YouTube Premium in the past.",
            parse_mode="Markdown"
        )
        # Store reward choice in user data for later retrieval when Gmail is provided
        user['pending_reward'] = {
            "type": choice,
            "name": reward_name,
            "cost": cost
        }
        save_data(data)
        return

    # For other rewards, process immediately
    user['points'] -= cost
    save_data(data)
    
    # Create order ID for tracking
    order_id = f"ORD{random.randint(10000, 99999)}"
    
    if 'orders' not in data:
        data['orders'] = {}
    
    # Save order info
    data['orders'][order_id] = {
        "user_id": str(message.chat.id),
        "username": message.chat.username or "NoUsername",
        "reward_type": choice,
        "reward_name": reward_name,
        "cost": cost,
        "status": "pending",
        "date": str(message.date),
        "gmail": None  # Will be None for non-YouTube rewards
    }
    save_data(data)
    
    confirmation = (
        f"✅ *Reward Redeemed Successfully!*\n\n"
        f"🎁 *{reward_name}*\n"
        f"🔖 Order ID: `{order_id}`\n"
        f"💰 Points spent: *{cost}*\n"
        f"💼 Remaining balance: *{user['points']}* points\n\n"
        f"🕒 Your reward will be processed soon.\n"
        f"📱 You'll receive account details via message."
    )
    
    bot.send_message(message.chat.id, confirmation, parse_mode="Markdown")

    # Notify Admin Channel about the request with improved formatting
    admin_notification = (
        f"<b>🎁 NEW REWARD REQUEST 🎁</b>\n\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        f"🏆 <b>Reward:</b> <b>{reward_name}</b>\n"
        f"🔖 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"👤 <b>User:</b> <code>{message.chat.id}</code> (@{message.chat.username or 'NoUsername'})\n"
        f"🔑 <b>Referral Code:</b> <code>{user['referral_code']}</code>\n"
        f"💰 <b>Points spent:</b> <b>{cost}</b>\n"
        f"🗃 <b>Wallet:</b> <code>{user['wallet'] or 'Not set'}</code>\n"
        f"🔍 <b>Status:</b> <b>⏳ Pending</b>\n"
        f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        f"⏱ <b>Requested:</b> {message.date}\n"
        f"🤖 <b>Via:</b> @{bot.get_me().username}\n\n"
        f"❗ <b>Note:</b> Bot cannot be used without a referral code."
    )
    
    bot.send_message(ADMIN_CHANNEL, admin_notification, parse_mode="HTML")

@bot.message_handler(commands=['gmail'])
def process_gmail(message):
    user_id = str(message.chat.id)
    user = get_or_create_user(user_id, message.chat.username)
    
    # Check if user has a pending YouTube Premium reward
    if not user.get('pending_reward') or user['pending_reward']['type'] != 'yt':
        bot.send_message(user_id, "❌ You don't have a pending YouTube Premium order.")
        return
    
    # Extract Gmail from command
    try:
        gmail = message.text.split(' ', 1)[1].strip().lower()
        
        # Simple validation
        if not '@gmail.com' in gmail:
            bot.send_message(user_id, "❌ Please provide a valid Gmail address (example@gmail.com).")
            return
            
        # Get the pending reward details
        reward_info = user['pending_reward']
        
        # Deduct points
        user['points'] -= reward_info['cost']
        
        # Create order ID
        order_id = f"ORD{random.randint(10000, 99999)}"
        
        # Initialize orders dict if not exists
        if 'orders' not in data:
            data['orders'] = {}
        
        # Save order with Gmail
        data['orders'][order_id] = {
            "user_id": user_id,
            "username": user.get('username', 'NoUsername'),
            "reward_type": reward_info['type'],
            "reward_name": reward_info['name'],
            "cost": reward_info['cost'],
            "status": "pending",
            "date": str(message.date),
            "gmail": gmail
        }
        
        # Remove pending reward
        del user['pending_reward']
        save_data(data)
        
        # Send confirmation
        confirmation = (
            f"✅ *YouTube Premium Order Confirmed!*\n\n"
            f"📧 Gmail: `{gmail}`\n"
            f"🔖 Order ID: `{order_id}`\n"
            f"💰 Points spent: *{reward_info['cost']}*\n"
            f"💼 Remaining balance: *{user['points']}* points\n\n"
            f"🕒 Your YouTube Premium will be activated soon.\n"
            f"📱 You'll receive account details via message."
        )
        
        bot.send_message(user_id, confirmation, parse_mode="Markdown")
        
        # Notify Admin
        admin_notification = (
            f"<b>🎬 NEW YOUTUBE PREMIUM REQUEST 🎬</b>\n\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            f"🔖 <b>Order ID:</b> <code>{order_id}</code>\n"
            f"👤 <b>User:</b> <code>{user_id}</code> (@{user.get('username', 'NoUsername')})\n"
            f"🔑 <b>Referral Code:</b> <code>{user['referral_code']}</code>\n"
            f"💰 <b>Points spent:</b> <b>{reward_info['cost']}</b>\n"
            f"🔍 <b>Status:</b> <b>⏳ Pending</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
            f"⏱ <b>Requested:</b> {message.date}\n"
            f"🤖 <b>Via:</b> @{bot.get_me().username}\n\n"
            f"❗ <b>Note:</b> Bot cannot be used without a referral code."
        )
        
        bot.send_message(ADMIN_CHANNEL, admin_notification, parse_mode="HTML")
        
    except IndexError:
        bot.send_message(user_id, "❌ Please use the format `/gmail youremail@gmail.com`")

@bot.message_handler(commands=['order'])
def show_orders(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ This command is only for admins.")
        return
        
    if 'orders' not in data or not data['orders']:
        bot.send_message(ADMIN_ID, "📭 No orders in queue.")
        return
        
    # Count orders by status
    pending_count = sum(1 for order in data['orders'].values() if order['status'] == 'pending')
    completed_count = sum(1 for order in data['orders'].values() if order['status'] == 'completed')
    
    reply = f"📋 *Orders Summary*\n\n"
    reply += f"🔄 Pending: {pending_count}\n"
    reply += f"✅ Completed: {completed_count}\n"
    reply += f"📊 Total: {len(data['orders'])}\n\n"
    
    # Show pending orders first, sorted by date (newest first)
    pending_orders = sorted(
        [(order_id, order) for order_id, order in data['orders'].items() if order['status'] == 'pending'],
        key=lambda x: x[1]['date'],
        reverse=True
    )
    
    if pending_orders:
        reply += "*Pending Orders:*\n\n"
        
        for order_id, order in pending_orders[:5]:  # Show only the 5 most recent orders
            reward_name = order['reward_name']
            username = order['username']
            date = order['date']
            reply += f"🔖 ID: `{order_id}`\n"
            reply += f"🎁 {reward_name}\n"
            reply += f"👤 @{username}\n"
            reply += f"⏱ Date: {date}\n"
            reply += f"✅ Complete with: `/done {order_id}`\n\n"
    
    bot.send_message(ADMIN_ID, reply, parse_mode="Markdown")

@bot.message_handler(commands=['done'])
def complete_order(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ This command is only for admins.")
        return
        
    try:
        order_id = message.text.split(' ', 1)[1].strip()
        
        if 'orders' not in data or order_id not in data['orders']:
            bot.send_message(ADMIN_ID, f"❌ Order ID `{order_id}` not found.")
            return
            
        order = data['orders'][order_id]
        
        if order['status'] == 'completed':
            bot.send_message(ADMIN_ID, f"⚠️ Order ID `{order_id}` is already marked as completed.")
            return
            
        # Mark as completed
        order['status'] = 'completed'
        order['completed_date'] = str(message.date)
        save_data(data)
        
        # Notify admin
        bot.send_message(
            ADMIN_ID, 
            f"✅ Order `{order_id}` marked as completed.",
            parse_mode="Markdown"
        )
        
        # Notify user
        user_notification = (
            f"🎉 *Good News!* Your order has been completed.\n\n"
            f"🔖 Order ID: `{order_id}`\n"
            f"🎁 Reward: *{order['reward_name']}*\n\n"
            f"Thank you for using our service! Enjoy your reward."
        )
        
        bot.send_message(int(order['user_id']), user_notification, parse_mode="Markdown")
        
    except IndexError:
        bot.send_message(ADMIN_ID, "❌ Please use the format `/done ORDER_ID`")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id != ADMIN_ID:
        return
    bot.send_message(ADMIN_ID, "✍️ Send the message to broadcast:")
    bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    for user_id in data.keys():
        bot.send_message(user_id, message.text)
    bot.send_message(ADMIN_ID, "✅ Broadcast sent!")

@bot.message_handler(commands=['user_list'])
def user_list(message):
    if message.chat.id != ADMIN_ID:
        return
    user_info = "\n".join([f"👤 @{user.get('username', 'NoUsername')} - ID: {user['chat_id']} - Points: {user['points']}" for user in data.values() if 'chat_id' in user])
    bot.send_message(ADMIN_ID, f"📋 User List:\n{user_info}")

@bot.message_handler(commands=['topup'])
def topup(message):
    if message.chat.id != ADMIN_ID:
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(ADMIN_ID, "❌ Use: /topup <username> <amount>")
            return

        username = args[1].replace("@", "")  # Remove @ if given
        amount = int(args[2])

        # Find user ID from username
        user_id = None
        for uid, user in data.items():
            if user.get("username") == username:
                user_id = uid
                break

        if user_id is None:
            bot.send_message(ADMIN_ID, f"❌ User @{username} not found!")
            return

        # Update points
        data[user_id]["points"] += amount
        save_data(data)

        bot.send_message(ADMIN_ID, f"✅ Successfully added {amount} points to @{username}!")
        bot.send_message(int(user_id), f"🎉 {amount} points have been added to your balance!")

    except ValueError:
        bot.send_message(ADMIN_ID, "❌ Invalid amount! Use /topup <username> <amount>")

@bot.message_handler(commands=['verify'])
def admin_verify(message):
    if message.chat.id != ADMIN_ID:
        return
        
    try:
        args = message.text.split()
        if len(args) != 2:
            bot.send_message(ADMIN_ID, "❌ Use: /verify <username>")
            return

        username = args[1].replace("@", "")  # Remove @ if given

        # Find user ID from username
        user_id = None
        for uid, user in data.items():
            if user.get("username") == username:
                user_id = uid
                break

        if user_id is None:
            bot.send_message(ADMIN_ID, f"❌ User @{username} not found!")
            return

        # Update verification status
        data[user_id]["verified"] = True
        data[user_id]["joined"] = True
        save_data(data)

        bot.send_message(ADMIN_ID, f"✅ Successfully verified @{username}!")
        bot.send_message(int(user_id), f"🎉 Your account has been verified by an admin!")

    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Error: {str(e)}")

bot.polling()
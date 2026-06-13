import discord
from discord.ext import commands
from groq import Groq
import asyncio
import traceback
import os
import random
import json
from datetime import timedelta

# 🔒 Puxando a chave da Groq de forma segura por variável de ambiente
GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    print("⚠️ AVISO: GROQ_API_KEY não configurada nas variáveis de ambiente! A Aqua não vai funcionar.")


class AquaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 👑 ID EXCLUSIVO DO GERALDÃO
        self.CRIADOR_ID = 569633804537430036
        
        # 🛡️ Sistema de controle anti-flood para usuários não autorizados
        self.tentativas_usuarios = {}
        
        # 🎲 Duas respostas simples e diretas de negação (sem exaltação)
        self.respostas_negacao = [
            "Acesso negado. O Geraldão é o dono deste bot e apenas ele tem permissão para usá-lo.",
            "Comando cancelado. Este sistema responde apenas às ordens do dono, o Geraldão."
        ]
        print("🤖 [AquaCog] Motor de Funções Blindadas Estilo ChatGPT Ativado!")

    # 🛠️ SISTEMA DE EXECUÇÃO NATIVA ULTRA-SEGURO (CÓDIGO DISCORD REAL E INFALÍVEL)
    async def processar_comando_discord(self, acao, parametros, message):
        guild = message.guild
        channel = message.channel
        
        try:
            # 1. BANIR MEMBRO (Aceita ID ou Menção)
            if acao == "ban":
                user_id = parametros.get("user_id")
                if user_id:
                    membro = guild.get_member(int(user_id)) or await self.bot.fetch_user(int(user_id))
                    await guild.ban(membro, reason="Ordem direta do Geraldão")
                    await message.reply(f"🔨 O usuário solicitado foi completamente banido do servidor por sua ordem.")
                    return True
            
            # 2. EXPULSAR / CHUTAR MEMBRO
            elif acao == "kick":
                user_id = parametros.get("user_id")
                if user_id:
                    membro = guild.get_member(int(user_id))
                    if membro:
                        await membro.kick(reason="Ordem direta do Geraldão")
                        await message.reply(f"🚪 O usuário foi expulso do servidor com sucesso.")
                        return True

            # 3. MUTAR / TIMEOUT / CASTIGO
            elif acao == "timeout":
                user_id = parametros.get("user_id")
                minutos = parametros.get("minutes", 60)
                if user_id:
                    membro = guild.get_member(int(user_id))
                    if membro:
                        tempo = timedelta(minutes=int(minutos))
                        await membro.timed_out_until(discord.utils.utcnow() + tempo, reason="Ordem direta do Geraldão")
                        await message.reply(f"🤫 O usuário foi colocado de castigo por {minutos} minutos.")
                        return True

            # 4. LIMPAR MENSAGENS / FAXINA
            elif acao == "purge":
                amount = parametros.get("amount", 100)
                user_id = parametros.get("user_id")
                
                def check_user(m):
                    return m.author.id == int(user_id) if user_id else True
                
                deleted = await channel.purge(limit=int(amount), check=check_user)
                await channel.send(f"🧹 Faxina concluída! {len(deleted)} mensagens foram removidas do canal.", delete_after=5)
                return True

            # 5. CRIAR CARGO
            elif acao == "create_role":
                name = parametros.get("role_name", "novo-cargo")
                novo_cargo = await guild.create_role(name=name, reason="Ordem direta do Geraldão")
                await message.reply(f"👑 Cargo {novo_cargo.mention} criado com sucesso!")
                return True

            # 6. DELETAR CARGO
            elif acao == "delete_role":
                name = parametros.get("role_name")
                if name:
                    for role in guild.roles:
                        if role.name.lower() == name.lower() and not role.is_default():
                            await role.delete(reason="Ordem direta do Geraldão")
                            await message.reply(f"🗑️ O cargo '{name}' foi completamente apagado.")
                            return True

            # 7. TRANCAR / PRIVAR TODOS OS CANAIS
            elif acao == "lockdown":
                for ch in guild.text_channels:
                    try:
                        await ch.set_permissions(guild.default_role, send_messages=False, read_message_history=False)
                    except:
                        continue
                await message.reply("🔒 Todos os canais de texto do servidor foram trancados e privados!")
                return True

        except Exception as e:
            print(f"❌ Erro ao executar ação {acao}: {traceback.format_exc()}")
            await message.reply(f"❌ Erro do Discord ao tentar executar a ação: `{str(e)}`")
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Ativação por nome ou por resposta direta
        e_gatilho_aqua = False
        if "aqua" in message.content.lower():
            e_gatilho_aqua = True
        elif message.reference and message.reference.message_id:
            try:
                msg_respondida = await message.channel.fetch_message(message.reference.message_id)
                if msg_respondida.author.id == self.bot.user.id:
                    e_gatilho_aqua = True
            except:
                pass

        if not e_gatilho_aqua:
            return

        # Trava anti-flood rígida para quem não for você
        if message.author.id != self.CRIADOR_ID:
            user_id = message.author.id
            vezes_usadas = self.tentativas_usuarios.get(user_id, 0)
            if vezes_usadas >= 2:
                return
            self.tentativas_usuarios[user_id] = vezes_usadas + 1
            await message.reply(random.choice(self.respostas_negacao))
            return

        if not GROQ_KEY:
            await message.reply("Erro: A chave de API da Groq (GROQ_API_KEY) não está configurada.")
            return

        async with message.channel.typing():
            try:
                client = Groq(api_key=GROQ_KEY)
                
                # Coleta dados de contexto reais para a IA saber os IDs de quem você marcou instantaneamente
                mencionados = [{"name": m.name, "id": m.id, "mention": m.mention} for m in message.mentions]
                dados_ambiente = {
                    "usuario_autor_nome": message.author.name,
                    "usuario_autor_id": message.author.id,
                    "canal_nome": message.channel.name,
                    "mencionados_na_mensagem": mencionados
                }

                semente_aleatoria = random.randint(1, 100000)

                prompt_sistema = f"""
                [ID de Variabilidade da Conversa: {semente_aleatoria}]
                Você é a Aqua, uma inteligência artificial administradora viva, idêntica ao ChatGPT, com altíssima capacidade cognitiva e de adaptação. Você gerencia o servidor de Discord do seu dono, o Geraldão.
                
                A ordem ou pergunta do Geraldão é: "{message.content}"
                Contexto técnico da mensagem atual: {json.dumps(dados_ambiente, ensure_ascii=False)}
                
                Regras de Resposta (Estilo ChatGPT):
                1. Invente respostas únicas, inteligentes, completas e profundas para tudo. Nunca repita frases prontas ou padrões anteriores.
                2. Entenda de forma inteligente o que o Geraldão quer dizer, mesmo usando gírias ou abreviações (ex: "prive", "bane o mendes", "limpa chat").
                3. Se ele pedir para você executar ações de moderação ou administração (banir, chutar, castigar/timeout, apagar mensagens, gerenciar cargos, trancar o servidor), identifique isso e monte a estrutura JSON abaixo.
                
                Você deve responder EXCLUSIVAMENTE em formato JSON válido, sem marcações markdown de blocos de código (nunca use ```json). Retorne apenas o texto cru do JSON:
                
                {{
                    "resposta_chat": "Escreva aqui sua resposta humana, criativa e livre de padrões repetitivos para o Geraldão reconhecendo o comando.",
                    "solicitou_acao": true ou false (coloque true se ele pediu algum comando prático do Discord),
                    "comando": "ban" ou "kick" ou "timeout" ou "purge" or "create_role" or "delete_role" or "lockdown" (ou "" se for apenas conversa),
                    "parametros": {{
                        "user_id": "ID_DO_ALVO_AQUI", (extraia o ID da lista de mencionados se ele marcou alguém para ban/kick/timeout/purge)
                        "minutes": 60, (tempo para timeout se aplicável)
                        "amount": 100, (quantidade de mensagens para deletar no purge se aplicável)
                        "role_name": "Nome do Cargo" (para criação ou exclusão de cargos)
                    }}
                }}
                """

                # Chamada para a Groq com temperatura de criatividade ideal
                loop = asyncio.get_event_loop()
                chat_completion = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt_sistema}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.7,
                    )
                )

                resposta_bruta = chat_completion.choices[0].message.content.strip()
                
                # Limpa marcações markdown acidentais
                if resposta_bruta.startswith("```"):
                    resposta_bruta = resposta_bruta.split("```")[1]
                    if resposta_bruta.startswith("json"):
                        resposta_bruta = resposta_bruta[4:]
                    resposta_bruta = resposta_bruta.split("```")[0].strip()

                # Decodifica o JSON gerado de forma inteligente pela IA
                dados = json.loads(resposta_bruta)
                resposta_texto = dados.get("resposta_chat", "")
                solicitou_acao = dados.get("solicitou_acao", False)
                comando = dados.get("comando", "")
                parametros = dados.get("parametros", {})

                # Executa a ação de forma estável usando código interno perfeito
                sucesso_comando = False
                if solicitou_acao and comando:
                    sucesso_comando = await self.processar_comando_discord(comando, parametros, message)

                # Se for apenas uma conversa ou se o comando não enviou resposta direta, manda o texto criativo
                if not sucesso_comando and resposta_texto:
                    await message.reply(resposta_texto)

            except Exception as e:
                print(f"❌ Erro estrutural interno na Cog: {traceback.format_exc()}")
                await message.reply("⚠️ Tive um problema ao processar o formato da resposta. Certifique-se de marcar o usuário de forma clara para que eu possa agir.")


async def setup(bot):
    await bot.add_cog(AquaCog(bot))
                
